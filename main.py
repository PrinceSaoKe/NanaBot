import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


def main() -> None:
    nonebot.init()

    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)

    nonebot.load_from_toml("pyproject.toml")
    nonebot.load_plugins("plugins")
    nonebot.run()


if __name__ == "__main__":
    main()
