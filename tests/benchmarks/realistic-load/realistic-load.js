import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = 'http://localhost:8000';
const N_BOARDS = 50;
const FIRST_BOARD_ID = 1;

// k6 calls this ONCE before the test; whatever it returns is passed to default(token)
export function setup() {
  const response = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({
      email: 'dummy_email_for_seeding@gmail.com',
      password: 'dummy_password_for_seeding',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  return response.json('access_token');
}

let headers;   // filled at the start of every session from the token that setup() returned

// 409 is an expected outcome of optimistic concurrency, not a failure
http.setResponseCallback(http.expectedStatuses({ min: 200, max: 204 }, 409));

const boardLoadLatency = new Trend('board_load_latency', true);
const writeLatency = new Trend('write_latency', true);

export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    realistic: {
      executor: 'ramping-arrival-rate',   // open model: new sessions start at a fixed rate, whether or not earlier ones have received their responses
      startRate: 5,
      stages: [
        { target: 10, duration: '20s' },  // ramp from 5 to 10 new sessions/s over 20s, evenly time spaced
        { target: 20, duration: '20s' },
        { target: 20, duration: '2m' },
        { target: 0, duration: '20s' },
      ],
    },
  }
};

// Skewed pick: a few hot boards get most of the traffic (squaring pushes toward index 0), so 25% of boards are called 50% of times (when random returns number less than 0.5)
function pickBoardId() {
  return FIRST_BOARD_ID + Math.floor(N_BOARDS * Math.pow(Math.random(), 2));
}

function think() {
  sleep(0.5 + Math.random() * 1.5);
}

function randomOf(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function write(op, method, url, body) {
  const res = http.request(method, url, body ? JSON.stringify(body) : null, { headers, tags: { op } });
  writeLatency.add(res.timings.duration, { op });

  // check that the endpoint returns the expected output
  check(res, { [`${op} ok or conflict`]: (r) => (r.status >= 200 && r.status < 300) || r.status === 409 });
}

function updateDetails(boardId, task) {
  write('update_details', 'PATCH',
    `${BASE_URL}/boards/${boardId}/columns/${task.column_id}/tasks/${task.id}/details`,
    { new_title: `Edited ${Date.now()}`, new_description: 'load test edit', version: task.version });
}

function moveTask(boardId, task, columns) {
  const dest = randomOf(columns);
  const last = dest.tasks.length ? dest.tasks[dest.tasks.length - 1].index : -1;
  write('move_task', 'PATCH',
    `${BASE_URL}/boards/${boardId}/columns/${task.column_id}/tasks/${task.id}/position`,
    { destination_column_id: dest.column_id, destination_predecessor_task_index: last, destination_successor_task_index: -1 });
}

function createTask(boardId, columns) {
  const col = randomOf(columns);
  write('create_task', 'POST',
    `${BASE_URL}/boards/${boardId}/columns/${col.column_id}/tasks/`,
    { task_title: `New ${Date.now()}`, task_description: 'load test task' });
}

// One iteration = one user session: open a board, then maybe edit it
export default function (token) {
  headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const boardId = pickBoardId();
  const res = http.get(`${BASE_URL}/boards/${boardId}/`, { headers, tags: { op: 'get_board' } });
  boardLoadLatency.add(res.timings.duration);

  // checks that all boards are retrieved successfully
  if (!check(res, { 'board 200': (r) => r.status === 200 }))
    return;

  const board = res.json();
  const columns = board.columns;
  const tasks = columns.flatMap((c) => c.tasks);
  if (tasks.length === 0) return;

  // ~80% read-only sessions, ~15% one write, ~5% two writes
  const r = Math.random();
  const nWrites = r < 0.80 ? 0 : r < 0.95 ? 1 : 2;

  for (let i = 0; i < nWrites; i++) {
    think();
    const w = Math.random();
    const task = randomOf(tasks);
    if (w < 0.6) updateDetails(boardId, task);              // 60% edit details
    else if (w < 0.9) moveTask(boardId, task, columns);     // 30% move (0.6 to 0.9)
    else createTask(boardId, columns);                      // 10% create
  }

  think();
}