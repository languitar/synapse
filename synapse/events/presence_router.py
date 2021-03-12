# -*- coding: utf-8 -*-
# Copyright 2021 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import TYPE_CHECKING, Dict, Iterable, List, Set, Tuple, Union, TypeVar

from synapse.handlers.presence import UserPresenceState

if TYPE_CHECKING:
    from synapse.server import HomeServer


class PresenceRouter:
    """
    A module that the homeserver will call upon to help route user presence updates to
    additional destinations. If a custom presence router is configured, calls will be
    passed to that instead.
    """

    # A constant used to specify that a user should receive presence updates
    # for all other users.
    ALL = TypeVar("ALL")

    def __init__(self, hs: "HomeServer"):
        self.custom_presence_router = None

        # Check whether a custom presence router module has been configured
        if hs.config.presence_router_module:
            # Initialise the module
            self.custom_presence_router = hs.config.presence_router_module_class(
                config=hs.config.presence_router_config, module_api=hs.get_module_api()
            )

    async def get_rooms_and_users_for_states(
        self,
        state_updates: Iterable[UserPresenceState],
    ) -> Tuple[Dict[str, List[UserPresenceState]], Dict[str, List[UserPresenceState]]]:
        """
        Given an iterable of user presence updates, determine where each one
        needs to go.

        Args:
            state_updates: An iterable of user presence state updates.

        Returns:
          A 2-tuple of (room_ids_to_states, users_to_states),
          with each item being a dict of entity_name -> [UserPresenceState].
        """
        if self.custom_presence_router is not None:
            # Ask the custom module
            return self.custom_presence_router.get_rooms_and_users_for_states(
                state_updates=state_updates
            )

        # Don't include any extra destinations for presence updates
        return {}, {}

    # get_interested_users is used to filter out presence up front
    # then get_users_for_state is used as a second filter

    # TODO: Should we also call this to do early filtering of incoming presence updates,
    # so the logic matches that of /sync?
    async def get_interested_users(self, user_id: str) -> Union[Set[str], ALL]:
        """
        Retrieve a list of users that the provided user is interested in receiving the presence of.
        Optionally, the constant ALL can be returned to mean that this user should receive all
        local and remote incoming presence.

        Note that this method will only be called for local users.

        Args:
            user_id: A user requesting presence updates.

        Returns:
            A set of user IDs to return presence updates for, or ALL to return all known updates.
        """
        if self.custom_presence_router is not None:
            if hasattr(self.custom_presence_router, "get_interested_users"):
                # Ask the custom module for interested users
                return await self.custom_presence_router.get_interested_in(
                    user_id=user_id
                )
            elif hasattr(self.custom_presence_router, "get_users_for_states"):
                # The custom module does not implement `get_interested_users`, but it does implement
                # `get_users_for_states`. In this state, the module may find that local users do not
                # receive all desired presence updates, as a presence update must satisfy both
                # functions in order to reach a local user.
                #
                # Given this, if get_users_for_states is defined, we just return ALL here.
                return PresenceRouter.ALL

        # A custom presence router is not defined, or doesn't implement any relevant function.
        # Don't report any additional interested users.
        return {}
