# GitHub Notifications Telegram Bot

This project is a Telegram bot that notifies you about GitHub notifications in real time.

## Requirements

- Docker
- Docker Compose (optional, for easier container management)
- A Telegram bot token
- A GitHub personal access token with notifications permissions

## Create a Telegram Bot

1. Open Telegram and search for the user `@BotFather`.
2. Start a conversation and use the `/newbot` command to create a new bot.
3. Follow the instructions to name your bot and obtain the access token.
4. Save the access token; you will need it later.

For more details, refer to the [official Telegram Bots documentation](https://core.telegram.org/bots#3-how-do-i-create-a-bot).

## Create a GitHub Personal Access Token (classic)

1. Go to [GitHub settings](https://github.com/settings/tokens).
2. Create a new personal access token with the `notifications` permission.
3. Save the token; you will need it later.

For more details, refer to the [official GitHub documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## Using Docker Compose

1. Clone this repository:

    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2. Create a `docker-compose.yml` file in the root of the project with the following content:

    ```yaml
    services:
      telegram-bot:
        build: .
        environment:
          - TELEGRAM_BOT_TOKEN=your_telegram_bot_token
          - GITHUB_CHECK_INTERVAL=60  # Interval in seconds (you can adjust it)
        restart: unless-stopped
    ```

3. Build and start the services defined in `docker-compose.yml`:

    ```sh
    docker-compose up --build -d
    ```

4. To check if the container is running, use:

    ```sh
    docker-compose ps
    ```

5. To stop the services:

    ```sh
    docker-compose down
    ```

## Using Docker without Docker Compose

1. Clone this repository:

    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2. Build the Docker image:

    ```sh
    docker build -t my-telegram-bot .
    ```

3. Run the Docker container with the necessary environment variables:

    ```sh
    docker run -d --name my-telegram-bot-container -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token -e GITHUB_CHECK_INTERVAL=60 my-telegram-bot
    ```

## Initialize the Bot

1. Open Telegram and search for your bot using the name you gave it.
2. Start a conversation with your bot and send the `/start` command. The bot will prompt you to provide your GitHub personal access token.
3. Reply with your GitHub personal access token.

4. If the token is valid, the bot will start sending you GitHub notifications.

## Documentation

- [Telegram Bots Documentation](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
- [GitHub Personal Access Tokens Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Contributions

Contributions are welcome! If you have suggestions, issues, or improvements, please open an issue or a pull request.

## License

This project is licensed under the MIT License.
