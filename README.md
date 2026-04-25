# envault

> A CLI tool for encrypting and versioning `.env` files using age encryption, with team sharing support.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

**Initialize a vault in your project:**

```bash
envault init
```

**Encrypt your `.env` file:**

```bash
envault lock .env
```

**Decrypt and load secrets:**

```bash
envault unlock .env.age
```

**Add a teammate's public key for shared access:**

```bash
envault share --key "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"
```

**Push a new version:**

```bash
envault commit -m "add stripe keys"
```

Encrypted files (`.env.age`) are safe to commit to version control. Never commit your raw `.env` file.

---

## How It Works

envault uses [age](https://github.com/FiloSottile/age) under the hood to encrypt secrets with recipient-based public key encryption. Each team member holds their own private key, and multiple recipients can be authorized per vault.

---

## Requirements

- Python 3.8+
- `age` binary installed ([install guide](https://github.com/FiloSottile/age#installation))

---

## License

MIT © 2024 envault contributors