from dataclasses import dataclass
from datetime import datetime, timedelta

MAX_CHANCE = 5
RESTART = 15  # restart after x minutes
REMOVE_TRY = 10

CAN_TRY = 1
BLOCKED = 2
ADDED = 3

@dataclass
class LResponse:
    status: int
    data: dict = None


@dataclass
class Source_info:
    ipaddr: str
    username: str


@dataclass
class Lock_source:
    src_info: Source_info
    expire: float


@dataclass
class Login_attempt:
    src_info: Source_info
    timestamps: []


class Login_manager:

    def __init__(self):
        self.user_attempts = []
        self.lock_user = []

    def can_try(self, source: Source_info):

        lock_index = self.is_block(source)

        if lock_index != -1:

            if self.lock_user[lock_index].expire <= datetime.now().timestamp():
                self.remove_from_lock_buff(lock_index)
                return LResponse(CAN_TRY)

            return LResponse(
                BLOCKED,
                {"blocked-until": self.lock_user[lock_index].expire}
            )

        return LResponse(CAN_TRY)

    def add_attempt(self, attempt: Source_info):

        index = self.have_attempt(attempt)

        if index != -1:
            self.user_attempts[index].timestamps.append(datetime.now().timestamp())
            self.remove_dated_try(index)

            if len(self.user_attempts[index].timestamps) - 1 >= MAX_CHANCE:
                self.lock_user.append(
                    Lock_source(
                        attempt,
                        (datetime.now() + timedelta(minutes=RESTART)).timestamp()
                    )
                )

            return LResponse(ADDED, {"try-left": MAX_CHANCE - (len(self.user_attempts[index].timestamps) - 1)})

        self.user_attempts.append(Login_attempt(attempt, [datetime.now().timestamp()]))
        return LResponse(ADDED, {"try-left": MAX_CHANCE - 1})

    def is_block(self, src_info: Source_info):

        i = 0
        for user in self.lock_user:

            if user.src_info == src_info:
                return i

        return -1

    def remove_from_lock_buff(self, index: int):

        self.lock_user.pop(index)

    def have_attempt(self, src_info: Source_info) -> int:

        i = 0
        for user in self.user_attempts:

            if user.src_info == src_info:
                return i

            i += 1

        return -1

    def remove_dated_try(self, index: int):

        tmp = self.user_attempts[index].timestamps
        i = 0

        for t in self.user_attempts[index].timestamps:
            if (t + timedelta(minutes=REMOVE_TRY).total_seconds()) <= datetime.now().timestamp():
                tmp.pop(i)

            i += 1

        self.user_attempts[index].timestamps = tmp

    def remove_user(self,source: Source_info):

        i = 0
        for user in self.user_attempts:

            if user.src_info == source:
                self.user_attempts.pop(i)
                break

            i += 1


