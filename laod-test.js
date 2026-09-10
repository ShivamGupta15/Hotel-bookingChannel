import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 50 },
    { duration: '20s', target: 100 },
    { duration: '20s', target: 200 },
    { duration: '20s', target: 300 },
    { duration: '10s', target: 0 },
  ],

  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

// Generate dates in dd-mm-yyyy format
function formatDate(date) {
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();

  return `${day}-${month}-${year}`;
}

export default function () {
  // Each iteration uses a different starting date
  const startDate = new Date(2026, 8, 10);

  // Spread requests across 21 different check-in dates
  const offset = (__ITER % 21);

  startDate.setDate(startDate.getDate() + offset);

  const checkIn = new Date(startDate);

  // 3-night stay
  const checkOut = new Date(startDate);
  checkOut.setDate(checkOut.getDate() + 3);

  const url =
    'http://localhost:8000/api/v1/availability/' +
    `?room_id=1` +
    `&check_in=${formatDate(checkIn)}` +
    `&check_out=${formatDate(checkOut)}`;

  const response = http.get(url);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response contains availability': (r) =>
      r.body.includes('"available"'),
  });
}