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

from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple

from synapse.handlers.presence import UserPresenceState

if TYPE_CHECKING:
    from synapse.server import HomeServer


class PresenceRouter:
    """
    A module that the homeserver will call upon to help route user presence updates to
    additional destinations. If a custom presence router is configured, calls will be
    passed to that instead.
    """

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
