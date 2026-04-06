import asyncio
import websockets
import os
from game_logic import handle_game_session

# 環境変数からIPとポートを取得（S1とS2で設定を変える）
# 例: S1では HOST=192.168.1.10, PORT=8081
# 例: S2では HOST=192.168.1.20, PORT=8081
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8081))

async def main():
    """WebSocketサーバーを起動する"""
    async with websockets.serve(handle_game_session, HOST, PORT):
        print(f"[S] Game Session Service listening on ws://{HOST}:{PORT}")
        await asyncio.Future()  # サーバーを永続的に実行

if __name__ == "__main__":
    asyncio.run(main())