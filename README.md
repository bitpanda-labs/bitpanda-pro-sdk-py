# Bitpanda Pro SDK

![release](https://github.com/bitpanda-labs/bitpanda-pro-sdk-py/workflows/bp-pro-sdk-release/badge.svg)

The [Bitpanda Pro](https://www.bitpanda.com/en/pro) SDK is a python reference implementation to easily interact with the web socket api.

## Development Status
The SDK is currently in Beta state and will move soon to a final version.
Please open an issue on Github if you have any change request or contact the [Official Bitpanda Support](https://support.bitpanda.com/hc/en-us/requests/new).

## Overview
Essentially the SDK consists of the `BitpandaProWebsocketClient` and the `AdvancedBitpandaProWebsocketClient`.

* The `BitpandaProWebsocketClient` handles all connect / subscribe / unsubscribe logic and forwards all received web socket messages via callbacks.
* The `AdvancedBitpandaProWebsocketClient` uses the `BitpandaProWebsocketClient` internally and has an additional state management depending on what channel subscriptions are available.
  * If subscribed to the order book channel also the order book state is available.
  * If subscribed to the account history or trading channel then open orders / balances / trades are available.

:memo: REST api is not yet supported.

## SDK Features
* subscribe / unsubscribing of web sockets channels
* authentication
* order creation / cancellation
* receive trading updates
* receive account history updates
  * account state management via advanced client
* receive order book updates
  * order book state management via advanced client

## Quickstart

Releases are available on [pypi](https://pypi.org/project/bitpanda-pro-sdk/).

All usage examples can be found in [bpprosdk/examples/websockets](/bpprosdk/examples/websockets).
Examples with the advanced client have the prefix `advanced_`

## Documentation
The official api documentation for BitpandaPro can be found here: https://developers.bitpanda.com/exchange/#websocket-api-overview

## Using the source
### Installation
Clone package:
```sh
git clone https://github.com/bitpanda-labs/bitpanda-pro-sdk-py
cd bitpanda-pro-sdk-py
```

Use pipenv:
```sh
pipenv install
pipenv sync --dev && pipenv shell
```

Run tests
```sh
export TEST_HOST=wss://streams.exchange.bitpanda.com
export BP_PRO_API_TOKEN=eyJ.....

pytest --log-cli-level DEBUG
```

Run Linter
```sh
pylint --rcfile=.pylintrc --output-format=parseable --reports=n bpprosdk
```

## Release

1. Bump the package version in `setup.py`.
1. Push a tag for the version (`vMAJOR.MINOR.PATH`) to trigger the release action on github.
