import http from 'k6/http';
import { check, sleep } from 'k6';


export const options = {
    vus: 100,
    duration: '20s'
};

const BASE_URL = 'http://localhost:8000';

export function setup() {
    const response = http.post(
        `${BASE_URL}/auth/login`,
        JSON.stringify({
            email: 'dummy_email_for_seeding@gmail.com',
            password: 'dummy_password_for_seeding',
        }),
        {
            headers: {
                'Content-Type': 'application/json',
            },
        }
    );

    return {
        token: response.json('access_token'),
    };
}

export default function (data) {
    const boardId = Math.floor(Math.random() * 50) + 1;    // to query random board every time and simulate the real-world behavior

    let res = http.get(`${BASE_URL}/boards/${boardId}/`, {
        headers: {
            Authorization: `Bearer ${data.token}`,
        }
    });

    check(res, { 'status 200': (r) => r.status === 200 });  // to check that all the numbers are for successful requests not errors

    sleep(1);
}