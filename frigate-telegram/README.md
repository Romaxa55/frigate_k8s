kubectl create secret generic frigate-telegram-bot-token \
  --from-literal=token='8018029633:AAFj0_dGG.......rXWqwYu6Y' -n frigate

helm upgrade --install frigate-telegram ./frigate-telegram \
  --set env.TELEGRAM_CHAT_ID=1080043984 -n frigate
