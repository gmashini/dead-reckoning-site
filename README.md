# Dead Reckoning — AI Simulation Projects

A collection of interactive AI probability and simulation tools.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Projects

### [Dead Reckoning](dead-reckoning/)

A probabilistic model mapping the risks and opportunities of artificial intelligence across the economy, software, society, politics, health, and more. Assigns each event a probability range, timing window, and impact assessment across 11 economic dimensions — then runs 20,000 Monte Carlo simulations to reveal the full distribution of possible futures.

### [March Madness 2026](march-madness/)

An XGBoost ML model + 20,000 Monte Carlo bracket simulations for NCAA March Madness. Dashboard shows model win probabilities vs. market odds, upset predictions, and round-by-round advancement percentages.

## Usage

Both projects are static HTML/CSS/JS — no build step required. Serve locally with any static file server:

```bash
npx serve . -l 3456
# Open http://localhost:3456
```

## License

[MIT](LICENSE)
