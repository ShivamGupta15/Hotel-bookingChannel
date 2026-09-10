import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const requestCount = Number(__ENV.REQUESTS || 10);
const expectedCapacity = Number(__ENV.CAPACITY || 1);
const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const roomId = Number(__ENV.ROOM_ID || 1);
const checkIn = __ENV.CHECK_IN || '10-09-2026';
const checkOut = __ENV.CHECK_OUT || '11-09-2026';

const successfulBookings = new Counter('successful_bookings');
const rejectedBookings = new Counter('rejected_bookings');
const serverErrors = new Counter('server_errors');

export const options = {
  scenarios: {
    concurrent_bookings: {
      executor: 'shared-iterations',
      vus: requestCount,
      iterations: requestCount,
      maxDuration: '30s',
    },
  },
  thresholds: {
    successful_bookings: [`count<=${expectedCapacity}`],
    server_errors: ['count==0'],
  },
};

function bookingPayload() {
  const iteration = `${__VU}-${__ITER}`;

  return JSON.stringify({
    room_id: roomId,
    guest_name: `Concurrency Test ${iteration}`,
    email: `concurrency-${iteration}@example.com`,
    phone: '9876543210',
    check_in: checkIn,
    check_out: checkOut,
    guests: 1,
  });
}

export default function () {
  const response = http.post(
    `${baseUrl}/api/v1/bookings/`,
    bookingPayload(),
    {
      headers: {
        'Content-Type': 'application/json',
      },
      tags: {
        test: 'concurrent-booking',
      },
    },
  );

  if (response.status === 200) {
    successfulBookings.add(1);
  } else if (response.status === 409) {
    rejectedBookings.add(1);
  } else if (response.status >= 500) {
    serverErrors.add(1);
  }

  check(response, {
    'booking accepted or rejected for availability': (result) =>
      result.status === 200 || result.status === 409,
    'no server error': (result) => result.status < 500,
  });
}

export function handleSummary(data) {
  const successful = data.metrics.successful_bookings?.values.count || 0;
  const rejected = data.metrics.rejected_bookings?.values.count || 0;
  const errors = data.metrics.server_errors?.values.count || 0;

  return {
    stdout: [
      'Concurrent booking test',
      `Requests: ${requestCount}`,
      `Successful bookings: ${successful}`,
      `Availability conflicts (409): ${rejected}`,
      `Server errors: ${errors}`,
      `Configured capacity: ${expectedCapacity}`,
      successful <= expectedCapacity
        ? 'Result: PASS - no overbooking detected'
        : 'Result: FAIL - successful bookings exceeded capacity',
    ].join('\n') + '\n',
  };
}
