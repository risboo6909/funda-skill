[![CI](https://github.com/risboo6909/funda-skill/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/risboo6909/funda-skill/actions/workflows/ci.yml)

# Funda Skill
Some notes for people who want to use this skill.

## Disclaimer

The author is not responsible for any issues that may occur while using this skill.  
Use it at your own risk.

## Short Description

This is my first experiment with agent skills, so please don’t judge too harshly 🙂  
At the same time, I’m very open to feedback and suggestions for improvement.

I originally built this skill for myself. OpenClaw supports running tasks on a schedule (cron), which makes it possible to do some very useful things, for example, receiving daily notifications in a messenger when new housing options appear on Funda.

Since this is an AI agent, you can describe your requirements in natural language (for example: location, price range, size, energy label, etc.). The agent can then:
- filter listings based on those criteria
- apply some basic analysis
- rank results by relevance

At some point I realized that this could also be useful for other people. Searching for housing in the Netherlands is painful, and many people rely on Funda. That’s why I decided to share this skill with the community.

This skill was developed specifically for **OpenClaw**. I have not tested it with other agent frameworks, so compatibility with other agents is not guaranteed.

## Important Note

The initial startup of the skill may take some time.  
If the agent does not respond immediately, this is expected.

On first run, the agent needs to:
- create a Python virtual environment
- install PyFunda and its Python dependencies
- start a local HTTP gateway

Security note: the gateway has no authentication or rate limiting. It should only be used in trusted local environments and binds to loopback (`127.0.0.1`) by default.

By default the gateway should be started on `127.0.0.1` (loopback) for safety.

If you want **ClawHub cron jobs** to access the gateway and send scheduled updates, start the server on `0.0.0.0` instead:

```bash
python scripts/funda_gateway.py --host 0.0.0.0 --port 9090 --timeout 10
```

Reason: in ClawHub, cron jobs may run in an isolated environment, so they may not be able to reach a service bound only to loopback.

Once the gateway (`funda_gateway.py`) is installed and running, subsequent requests should be much faster.

## How It Works

The setup is intentionally simple.

The agent starts a local HTTP server that acts as a gateway between the agent and the Funda API.  
The agent sends HTTP requests to this local server, and the server:
- calls the Funda API via [PyFunda](https://github.com/0xMH/pyfunda)
- processes the results
- returns structured data back to the agent

The gateway is written in Python and kept intentionally minimal.  
This reduces errors, makes agent interaction more reliable, and allows new features to be added later with minimal changes if needed.

## Final Words

If you find this skill useful, please consider giving it a star on GitHub and sharing it with friends who are also searching for housing in the Netherlands.

Thanks!

[github repo](https://github.com/risboo6909/funda-skill)
