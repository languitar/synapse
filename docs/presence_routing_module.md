# Presence Routing Module

Synapse supports configuring a module that can specify additional destinations (users or
rooms) to receive certain presence updates from local users.

Both local or remote users can be specified as a destination. If a room is specified, that
will be translated to all users in that room. The homeserver must be participating in any
specified room.

The presence routing module is implemented as a Python class, which will be imported by
the running Synapse.

## Python Presence Router Class

The Python class is instantiated with two objects:

* Some configuration object (see below).
* An instance of `synapse.module_api.ModuleApi`.

It then implements methods related to presence routing.

Note that one method of `ModuleApi` that may be useful is:

```python
ModuleApi.send_local_online_presence_to(users: List[str]) -> None
```

which can be given a list of local or remote MXIDs to broadcast local user
presence to (for those users that the receiving user is considered interested in). 
It does not include state for users who are currently offline.

### Example

Below is an example implementation of a presence router class.

```python
from typing import Dict, Iterable, List, Tuple

from synapse.handlers.presence import UserPresenceState
from synapse.module_api import ModuleApi

class PresenceRouterConfig:
    def __init__(self):
        # Config options with their defaults

        # A list of users to always send all user presence updates to
        self.always_send_to_users = []  # type: List[str]

        # A dictionary of user IDs and the IDs of rooms that their updates
        # should be sent to the members of
        self.users_to_rooms = {}  # type: Dict[str, str]

class ExamplePresenceRouter:
    """An example implementation of synapse.presence_router.PresenceRouter.
    Supports routing all presence to a configured set of users, or a subset
    of presence from certain users to members of certain rooms.

    Args:
        config: A configuration object.
        module_api: An instance of Synapse's ModuleApi.
    """
    def __init__(self, config: PresenceRouterConfig, module_api: ModuleApi):
        self._config = config
        self._module_api = module_api

    @staticmethod
    def parse_config(config_dict: dict) -> PresenceRouterConfig:
        """Parse a configuration dictionary from the homeserver config, do
        some validation and return a typed PresenceRouterConfig.

        Args:
            config_dict: The configuration dictionary.

        Returns:
            A validated config object.
        """
        # Initialise a typed config object
        config = PresenceRouterConfig()

        always_send_to_users = config_dict.get("always_send_to_users")
        users_to_rooms = config_dict.get("users_to_rooms")

        # Do some validation of config options... otherwise raise a
        # synapse.config.ConfigError.

        config.always_send_to_users = always_send_to_users
        config.users_to_rooms = users_to_rooms

        return config

    async def get_rooms_and_users_for_states(
        self,
        state_updates: Iterable[UserPresenceState],
    ) -> Tuple[Dict[str, List[UserPresenceState]], Dict[str, List[UserPresenceState]]]:
        """Given an iterable of user presence updates, determine where each one
        needs to go.

        Args:
            state_updates: An iterable of user presence state updates.

        Returns:
          A 2-tuple of (room_ids_to_states, users_to_states),
          with each item being a dict of entity_name -> [UserPresenceState].
        """
        destination_rooms = {}  # type: Dict[str, List[UserPresenceState]
        destination_users = {}  # type: Dict[str, List[UserPresenceState]

        # Send all presence updates to specific users
        for user_id in self._config.always_send_to_users:
            destination_users[user_id] = state_updates

        # Map state updates for configured users to members of configured rooms
        for state in state_updates:
            room_id = self._config.users_to_rooms.get(state.user_id)
            if room_id:
                # Send state update for this user to the users in the room
                destination_rooms.setdefault(room_id, []).append(state.user_id)

        return destination_rooms, destination_users
```

## Configuration

Once you've crafted your module and installed it into the same Python environment as
Synapse, amend your homeserver config file with the following.

```yaml
presence:
  routing_modules:
    - module: my_module.ExamplePresenceRouter
      config:
        # Any configuration options for your module. The below is an example.
        # of setting options for ExamplePresenceRouter.
        always_send_to_users: ["@presence_gobbler:example.org"]
        users_to_rooms:
          - "@alice:example.com":
            - "!room1:example.org"
            - "!room2:example.net"
        ...
```

The contents of `config` will be passed as a Python dictionary to the static
`parse_config` method of your class. The object returned by this method will
then be passed to the `__init__` method of your module as `config`.