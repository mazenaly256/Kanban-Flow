import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://localhost:8000';
const BOARD_ID = 1;
const COLUMN_ID = 1;

export const options = {
  summaryTrendStats: ['avg', 'med', 'p(95)', 'max'],
  scenarios: {
    creates: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1s',
      duration: '1m',
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ email: 'dummy_email_for_seeding@gmail.com', password: 'dummy_password_for_seeding' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  return res.json('access_token');
}

export default function (token) {
  const res = http.post(
    `${BASE_URL}/boards/${BOARD_ID}/columns/${COLUMN_ID}/tasks/`,
    JSON.stringify({ task_title: `New ${Date.now()}`, task_description: 'load test' }),
    { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
  );
  check(res, { 'created': (r) => r.status >= 200 && r.status < 300 });
}