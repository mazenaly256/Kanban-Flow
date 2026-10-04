import http from 'k6/http';
import { Counter } from 'k6/metrics';


export const options = {
  scenarios: {
    concurrentUsers: { executor: 'per-vu-iterations', vus: 20, iterations: 1 }  // send one request and stops
  }
};

const noContent204 = new Counter('updates_accepted');
const conflict409 = new Counter('updates_rejected');


const URL = `http://localhost:8000/boards/${1}/columns/${1}/tasks/${2}/details/`;

export function setup() {
  const res = http.post(
    'http://localhost:8000/auth/login/',   // adapt to your login route
    JSON.stringify({ email: 'dummy_email_for_seeding@gmail.com', password: 'dummy_password_for_seeding' }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  return res.json('access_token');
}

export default function (token) {
  const res = http.patch(
    URL,
    JSON.stringify({ new_title: `VU ${__VU}`, new_description: 'race', version: 1 }),
    { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } },
  );

  if (res.status === 204)
    noContent204.add(1);

  else if (res.status === 409)
    conflict409.add(1);
}