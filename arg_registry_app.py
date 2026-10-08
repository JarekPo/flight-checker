from typing import ClassVar

from base_app import BaseApp


class ArgRegistryApp(BaseApp):
    ARG_HELP: ClassVar[dict[str, str]] = {
        'from-airport': 'Departure airport IATA code',
        'to-airport': 'Arrival airport IATA code',
        'topic': 'Notification topic',
    }
    use_args: ClassVar[tuple[str, ...]] = ()

    def add_args(self):
        if not self.use_args:
            raise NotImplementedError(f'{type(self).__name__} must define use_args')
        parser = super().add_args()
        for name in self.use_args:
            parser.add_argument(f'--{name}', required=True, help=self.ARG_HELP[name])
        return parser
