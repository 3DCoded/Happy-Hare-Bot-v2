# Happy Hare Bot v2
### by 3DCoded

![](https://github.com/moggieuk/Happy-Hare/wiki/resources/happy_hare_logo.jpg)

The bot supports the following commands:
- `!ui`
    Sends a reminder to check the pinned messages for Mainsail/Fluidd installation.

    This command outputs the following:

    ```
    PLEASE don't ask us how to install Mainsail or Fluidd HH Edition. Just check the pinned messages. 😃
    ```

- `!code @user`
    Tells the user how to properly format code blocks.

    This command outputs the following:

    @user When posting configs or logs, please surround with code fences (\`\`\`) so that Discord formats them correctly. Example:

    \`\`\`ini

    [mcu]

    serial: /dev/serial/by-id/usb-klipper-12345-if00

    \`\`\`

    ```ini            
    [mcu]
    serial: /dev/serial/by-id/usb-klipper-12345-if00
    ```
- `/code @user`

    Same function as !code @user, but this is restricted to admins.
- `!say <text>`

    Reserved for admin-listed users. Sends a message containing `<text>`.

Other features:

- When a message is sent in the `#mainsail-fluidd` channel containing both "how" AND "?", the UI message is sent, but frendlier.

## Installing

Just check the pinned messages. 😃