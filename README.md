# Singularity Technologies CLI

This CLI is desinged to help Engineers engage with our API and platform much
more easily.

The CLI handles HMAC signature generation and sets all necessary headers
autonomously.

Its highly recomended that you use the CLI rather than cURL commands.

The CLI has been tested on Ubuntu. If you require support or bug fixes for OSX
or Windows operating systems please open an issue!

Pull Requests are always welcome!

## Installation

The CLI can easily be installed using pip:

```
pip3 install singularitytechnologies.singularity-cli
```

We only officially support usage with Python3.5+

## Config file

The CLI will look for a config json file in the location:

```
$HOME/.singularity/config.json
```

Which should contain the following:

```
{
  "api_key": <key>,
  "secret": <secret>
}
```

If you'd like to store your config elsewhere, simply set the environment
variable:

```
SINGULARITY_CONFIG_PATH=<path>
```

## Usage

A full list of commands can be seen by simply using the following command:

```
singularity-cli
```

You can test your connection to the API by using our PING command:

```
singularity-cli ping
```

A successful connection should return the response `pong`

See this [blog post](https://www.singularity-technologies.io/blog) for a short demonstration on how to use the various
features of the CLI.
