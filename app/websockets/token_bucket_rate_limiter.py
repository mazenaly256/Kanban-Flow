import time


class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = capacity
        self._refill_rate = refill_rate   # tokens/second
        self._buckets: dict[int, tuple[float, float]] = {}      # user_id -> (available_tokens, last_refill_time)


    def allow(self, user_id):   # determines whether the request withing the limit or not
        if user_id not in self._buckets:
            self._buckets[user_id] = (self._capacity, time.monotonic())

        time_elapsed_from_last_refill = time.monotonic() - self._buckets[user_id][1]

        self._buckets[user_id] = (min(self._buckets[user_id][0] + time_elapsed_from_last_refill * self._refill_rate, self._capacity), time.monotonic())

        if self._buckets[user_id][0] >= 1:
            self._buckets[user_id] = (self._buckets[user_id][0] - 1, self._buckets[user_id][1])
            return True

        return False




rate_limiter = TokenBucketRateLimiter(capacity=5, refill_rate=0.5)      # add 1 token every 2 seconds till reach 5 tokens