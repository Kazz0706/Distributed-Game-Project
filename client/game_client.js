// // マッチングAPIのレスポンスを想定: 
// // { status: "matched", server_ip: "192.168.1.20", server_port: 8081, players: [...] }

// function connectToGameServer(match_result) {
//     const { server_ip, server_port, players, mode } = match_result;
    
//     // マッチングIDは、サーバー側で生成しクライアントに渡す必要があります。
//     // 今回は簡単のため、プレイヤーリストを元に仮のIDを使用
//     const session_id = players.sort().join('_');
//     const user_id = "CURRENT_USER_ID"; // ログイン情報から取得

//     const ws_url = `ws://${server_ip}:${server_port}/session/${session_id}?user_id=${user_id}`;
    
//     const socket = new WebSocket(ws_url);

//     socket.onopen = () => {
//         console.log("Connected to game session:", session_id);
//     };

//     socket.onmessage = (event) => {
//         // 他のプレイヤーからの入力メッセージを受信
//         const input_data = JSON.parse(event.data);
        
//         // 受信した入力データに基づき、画面上でキャラクターを動かす
//         // (ここで入力予測やロールバックなどのロジックが実行される)
//         handleRemoteInput(input_data); 
//     };

//     // プレイヤーの入力が発生したとき
//     document.addEventListener('keydown', (e) => {
//         const input_message = {
//             action: e.key,
//             frame: getCurrentGameFrame(), // 現在のゲームフレーム番号
//             user: user_id
//         };
//         // サーバーへ自分の入力情報を送信
//         socket.send(JSON.stringify(input_message)); 
//     });
// }

// A. 設定と状態管理
const BASE_URL = 'http://192.168.200.102:8000'; // ブラウザのURLと合わせる
// Nginxのパス設定
// const S1_AUTH_API_PATH = '/api/auth/login'; // Nginxのパス
// const S1_MATCH_API_PATH = '/api/game/match'; // Nginxのパス

// // マッチングAPIのURLは、BASE_URLとNginxのパスを結合して構築する
// // 以前の 'http://127.0.0.1:8080/match' を置き換える
// const S1_MATCH_URL = `${BASE_URL}${S1_MATCH_API_PATH}`; 
// // 認証APIも絶対パスで使うなら同様に設定しておくのが望ましい
// // const S1_AUTH_URL = `${BASE_URL}${S1_AUTH_API_PATH}`; 

// S1 Nginxコンテナが公開しているIPアドレスとポートを使用
const S1_AUTH_URL = 'http://192.168.200.102:8000/api/auth/login'; // S1 NginxのIPアドレスとNginxのパスに合わせる
const S1_MATCH_URL = 'http://192.168.200.102:8000/api/game/match'; // S1 NginxのIPアドレスとNginxのパスに合わせる
// 定数: アニメーションのスピードを制御
const RUN_CYCLE_SPEED = 0.30; // 周期の速さ

let CURRENT_USER_ID = null;
let WEBSOCKET = null;
let GAME_STATE = {};
let GAME_FRAME = 0; // ゲームフレームカウンター

// B. DOM要素の取得
const authSection = document.getElementById('authSection');
const mainContent = document.getElementById('mainContent');
const authMessage = document.getElementById('authMessage'); // 新しく追加

const matchSection = document.getElementById('match-section');
const gameSection = document.getElementById('game-section');
const matchMessage = document.getElementById('match-message');
const matchButton = document.getElementById('match-button');
const cancelButton = document.getElementById('cancel-button');
const canvas = document.getElementById('game-screen');
const ctx = canvas.getContext('2d');


// ログイン成功時の処理を関数化
function handleLoginSuccess(username) {
    CURRENT_USER_ID = username; // ★★★ ここでCURRENT_USER_IDを設定 ★★★
    authSection.classList.add('hidden'); // 認証セクションを非表示に

    // ★★★ ここで mainContent の hidden クラスを削除する ★★★
    mainContent.classList.remove('hidden'); // これがないとずっと隠れたまま
    // mainContent の display: none; を上書きするために直接スタイルを操作するか、
    // CSSで #mainContent.active { display: block; } のようなクラスを用意する。
    // mainContent.style.display = 'block'; // ★★★ mainContentを強制的に表示 ★★★

    // 必要であれば、マッチングセクションなどもここで制御
    document.getElementById('match-section').classList.remove('hidden');
    // document.getElementById('game-section').classList.add('hidden'); // ゲームセクションは初期は隠しておく
    // startGame(username); // ゲーム開始処理 (この時点ではマッチング画面なので不要)
}

// C.(a)ユーザー登録処理
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const email = document.getElementById('registerEmail').value; // emailフィールドを追加

    try {
        const response = await fetch('/api/auth/register', { // Nginxのパスに合わせる
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, email }) // emailを追加
        });
        const data = await response.json();
        authMessage.textContent = data.message; // メッセージを表示
        if (response.ok) {
            // 登録成功、ログインフォームに切り替えるなど
            document.getElementById('loginUsername').value = username;
            document.getElementById('loginPassword').value = password;
            // ユーザーに承認待ちであることを伝える
        }
    } catch (error) {
        authMessage.textContent = 'Registration failed: ' + error.message;
        console.error('Registration error:', error);
    }
});

// C(b).ユーザーログイン処理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch('/api/auth/login', { // Nginxのパスに合わせる
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        authMessage.textContent = data.message; // メッセージを表示
        if (response.ok) {
            handleLoginSuccess(username); // ログイン成功時の処理を呼び出し
            // ログイン成功時のメッセージが「ログインしました！」のようなものでない場合
            // authMessage.textContent = "ログインしました！";
        }else {
            // ログイン失敗時のメッセージは data.message に含まれるはず
            authMessage.textContent = data.message || 'ログインに失敗しました。';
        }
    } catch (error) {
        authMessage.textContent = 'Login failed: ' + error.message;
        console.error('Login error:', error);
    }
});

// D. マッチング処理
matchButton.addEventListener('click', () => {
    const selectedMode = document.querySelector('input[name="mode"]:checked').value;
    requestMatchmaking(selectedMode);
});

async function requestMatchmaking(mode) {
    if (!CURRENT_USER_ID) {
        matchMessage.textContent = 'マッチングエラー: user_idが設定されていません。ログインしてください。';
        matchButton.disabled = false;
        cancelButton.classList.add('hidden');
        console.error("Attempted to match without a CURRENT_USER_ID.");
        return; // リクエストを送信せずに終了
    }

    matchButton.disabled = true;
    cancelButton.classList.remove('hidden');
    matchMessage.textContent = `[${mode}] マッチングキュー待機中...`;

    try {
        const response = await fetch(S1_MATCH_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: CURRENT_USER_ID, mode })
        });

        const data = await response.json();
        
        if (data.status === 'matched') {
            matchMessage.textContent = `マッチング成立! 接続先: ${data.server_ip}:${data.server_port}`;
            // E. ゲームサーバーへの直接接続
            connectToGameServer(data);
        } else if (data.status === 'waiting') {
            // 待機中のフィードバック
            matchMessage.textContent = `[${mode}] 待機中... ${data.queue_size}/${data.required} 人`;
            // 待機中はポーリング（短い間隔でAPIを呼び出し）で状況を確認する
            setTimeout(() => requestMatchmaking(mode), 3000); 
        } else {
            matchMessage.textContent = `マッチングエラー: ${data.message}`;
            matchButton.disabled = false;
            cancelButton.classList.add('hidden');
        }

    } catch (error) {
        matchMessage.textContent = 'エラー: マッチングサーバーに接続できません。';
        console.error('Matchmaking error:', error);
        matchButton.disabled = false;
        cancelButton.classList.add('hidden');
    }
}

// E. ゲームサーバーへの直接接続とゲーム実行の部分の修正
function connectToGameServer(match_result) {
    const { server_ip, server_port, players, mode } = match_result;

    // S1, S2のゲームセッションに接続するために、ポートを8081または8082に設定
    // Docker Compose環境では、ホストのポートを直接使う
    const ws_host = `${server_ip}:${server_port}`; 

    // config.pyから返されたポートをそのまま使う
    const actual_ws_port = server_port; 
    const session_id = players.sort().join('_'); 

    // WebSocket URLを構築
    const ws_url = `ws://127.0.0.1:${actual_ws_port}/session/${session_id}?user_id=${CURRENT_USER_ID}`;
    
    WEBSOCKET = new WebSocket(ws_url);

    WEBSOCKET.onopen = () => {
        matchSection.classList.add('hidden');
        gameSection.classList.remove('hidden');
        GAME_STATE = {}; // サーバーからの初期状態を待つ
        // GAME_STATE = initializeGameState(players); // ゲーム状態の初期化
        requestAnimationFrame(gameLoop); // ゲームループ開始
    };


    WEBSOCKET.onmessage = (event) => {
        const server_message = JSON.parse(event.data);
        
        if (server_message.type === 'state_update') {
            // ★★★ サーバーからの最新の状態に上書き ★★★
            GAME_STATE = server_message.state; 
            
        } else if (server_message.type === 'game_over') {
            // ★★★ ゲーム終了メッセージの処理 ★★★
            alert(`GAME OVER! Winner: ${server_message.winner}`);
            WEBSOCKET.close(); // WebSocket接続をクローズ
        }
    };
    
    WEBSOCKET.onclose = () => {
        alert("ゲームセッションが終了しました。");
        // 成績更新APIを呼び出すなどの終了処理
        // sendFinalScores(GAME_STATE); 
        location.reload(); // 簡易的な終了処理
    };
}
// E. IMPORTANT: Docker ComposeでS1ホスト上にS1とS2をシミュレーションしているため、
    // S2のIP (192.168.200.103) を使わず、S1のIP (192.168.200.102) を使う。
    // そして、ポート番号を8081または8082に切り替える。
    // let actual_ws_port;
    // if (server_ip === '192.168.200.102') {
    //     actual_ws_port = 8081; // S1のゲームセッション
    // } else if (server_ip === '192.168.200.103') {
    //     actual_ws_port = 8082; // S2のゲームセッション (ホストの8082にマッピングされている)
    // } else {
    //     console.error("Unknown server IP returned from matching.");
    //     return;
    // }

    // const ws_url = `ws://192.168.200.102:${actual_ws_port}/session/${session_id}?user_id=${CURRENT_USER_ID}`;

    // 以下の行を、Docker Compose環境に合わせて変更する (S1/S2のIPアドレスを使用)
    // 注意: S1/S2のIPアドレスがクライアントから直接アクセスできることを前提とします。
    // S2(192.168.200.103)もVPN経由でアクセスできるなら、以下でOKです。

// F. ゲームロジックの簡易実装
function initializeGameState(players) {
    // プレイヤーの位置などの初期状態を定義
    // const state = {};
    // players.forEach((p, i) => {
    //     state[p] = { x: 50 + i * 150, y: 400, health: 100 };
    // });
    // return state;

    // サーバーが初期状態を返すため、ここでは空か簡易的なものにする
    return {};
}


// ★★★ キャラクターを描画する関数 ★★★
function drawCharacter(ctx, state, is_local_player) {
    const char_width = 30;
    const char_height = 80;
    const x = state.x;
    const y = state.y;
    
    // 描画の中心座標
    const center_x = x + char_width / 2;
    const center_y = y + char_height / 2;

    // --- 1. 色とスタイルの決定 ---
    let color = is_local_player ? 'blue' : 'red';
    if (state.state === 'hit') color = 'purple';
    
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 5; // 棒を太くする

    // アニメーション周期計算 (0から2π)
    const anim_phase = Math.sin(GAME_FRAME * RUN_CYCLE_SPEED); 
    const facing_dir = state.facing === 'right' ? 1 : -1;
    // const is_active_state = state.state === 'running' || state.state === 'attacking';
    
    // 描画の基準定数
    const head_radius = 12;
    const shoulder_y = y + head_radius * 2;
    const hip_y = center_y + 10;
    const arm_length = 35; // 腕の長さ (修正)
    const leg_length = 40; 
    
    // --- 1. 状態に応じた描画パラメータの設定 ---
    let arm_angle_offset = 0; // 腕の振りや開き
    let leg_angle_offset = 0; // 脚の振りや開き
    
    // デフォルトポーズ: 軽く開く
    if (state.state === 'idle' || state.state === 'hit' || state.state === 'jumping') {
        arm_angle_offset = 0.5; // 腕を少し開く
        leg_angle_offset = 0.3; // 脚を少し開く
    }

    if (state.state === 'running') {
        // 走る動作: 三角関数で周期的に値を変更
        arm_angle_offset = anim_phase * 0.5;
        leg_angle_offset = anim_phase * 0.5; 
    } 
    if (state.state === 'attacking') {
        // 攻撃中は、通常の腕・脚は描画しない（T字回避のため）
        arm_angle_offset = 0; 
        leg_angle_offset = 0;
    }
    
    // --- 2. 描画パス ---
    // 頭
    ctx.beginPath();    // ここからパスの記録を開始
    ctx.arc(center_x, y + head_radius, head_radius, 0, Math.PI * 2);
    ctx.fill(); // 頭を塗りつぶし
    ctx.stroke();   // 頭の輪郭を描画（オプション）
    // 胴体
    ctx.beginPath(); 
    ctx.moveTo(center_x, shoulder_y);
    ctx.lineTo(center_x, hip_y);

    // --- 腕 (攻撃中でない時) ---
    if (state.state !== 'attacking') {
        // 腕 (手前側: 正相)
        ctx.moveTo(center_x, shoulder_y);
        ctx.lineTo(center_x + facing_dir * arm_angle_offset * 15, shoulder_y + arm_length);

        // 腕 (奥側: 逆相)
        ctx.moveTo(center_x, shoulder_y);
        ctx.lineTo(center_x - facing_dir * arm_angle_offset * 15, shoulder_y + arm_length);
    }
    
    // --- 脚 ---
    // 右脚
    ctx.moveTo(center_x, hip_y);
    ctx.lineTo(center_x + leg_angle_offset * 15, hip_y + leg_length); 

    // 左脚
    ctx.moveTo(center_x, hip_y);
    ctx.lineTo(center_x - leg_angle_offset * 15, hip_y + leg_length);
    
    ctx.stroke(); // 胴体、腕、脚の線画をここで実行
    
    // ★★★ 3. 攻撃描画 (拳の生成と突き出し) ★★★
    if (state.state === 'attacking') {
        const attack_type = state.attack_type;
        const punch_radius = head_radius / 2; // 頭の1/2の半径
        let target_x = center_x;
        let target_y = shoulder_y;
        
        // 攻撃方向の調整
        if (attack_type === 'attack_forward' || attack_type === 'attack_super') {
            target_x = center_x + facing_dir * (arm_length + punch_radius + 5);
            target_y = shoulder_y + 5;
        } else if (attack_type === 'attack_up') {
            target_x = center_x + facing_dir * 5;
            target_y = shoulder_y - (arm_length + punch_radius + 5);
        } else if (attack_type === 'attack_down') {
            target_x = center_x + facing_dir * 5;
            target_y = hip_y + (arm_length + punch_radius + 5);
        }

        // 腕の線（突き出し）
        ctx.beginPath();
        ctx.moveTo(center_x, shoulder_y);
        ctx.lineTo(target_x, target_y);
        ctx.stroke();
        
        // 拳の描画
        ctx.fillStyle = 'black'; // 拳を黒くする
        ctx.arc(target_x, target_y, punch_radius, 0, Math.PI * 2);
        ctx.fill();

        if (attack_type === 'attack_super') {
            // 必殺技は頭と同じ大きさの拳
            ctx.beginPath();
            ctx.fillStyle = 'red';
            ctx.arc(target_x, target_y, head_radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    ctx.stroke(); 
}

function gameLoop() {
    GAME_FRAME++;
    
    // 描画(体力と状態の表示) 
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // ★★★ ステージの台を描画 ★★★
    const CANVAS_WIDTH = 640;
    const CANVAS_HEIGHT = 480;
    const PLATFORM_WIDTH = CANVAS_WIDTH * 2 / 3;
    const PLATFORM_TOP_Y = CANVAS_HEIGHT * 2 / 3; // 台の上部Y座標 (160px)
    const STAGE_LEFT_BOUNDARY = (CANVAS_WIDTH - PLATFORM_WIDTH) / 2;
    
    ctx.fillStyle = 'saddlebrown'; // 台の色
    ctx.fillRect(STAGE_LEFT_BOUNDARY, PLATFORM_TOP_Y, PLATFORM_WIDTH, 20); // 高さ20pxの台
    
    // プレイヤーを描画する前に、描画する順番を決める（X座標順など）
    const sortedPlayers = Object.keys(GAME_STATE).sort((a, b) => GAME_STATE[a].x - GAME_STATE[b].x);

    // ★★★ ループ内の描画ロジックを整理 ★★★
    for (const player of sortedPlayers) {
        const state = GAME_STATE[player];
        // 死亡したキャラクターは描画しないか、特別な描画にする
        if (state.state === 'dead') continue;
        
        // 2-A. キャラクター本体の描画 (drawCharacter関数を使用)
        drawCharacter(ctx, state, player === CURRENT_USER_ID); 
        // 2-B. UI情報 (ゲージとテキスト) の描画
        const char_width = 30; // drawCharacter内で使用される幅
        const info_x = (player === sortedPlayers[0]) ? 50 : 350; // プレイヤー1は左、プレイヤー2は右
        const info_y = 30; // 上部固定

        // --- 2. ゲージの描画（常に上部に表示） ---
        if (typeof state.meter === 'number') { // meterが数値であることを確認
            const max_meter_width = char_width;  // ゲージの最大幅
            const meter_height = 5;     // ゲージの高さ
            // ゲージの現在の幅を計算 (0-100の値を0-30の幅にマッピング)
            const current_meter_width = state.meter * max_meter_width / 100; 
            // const meter_y = draw_y + 85; // キャラクターの足元より少し下に描画
            const meter_y = state.y - 25; 
            
            // 2.1. ゲージの枠（背景）を描画
            ctx.fillStyle = 'gray';
            ctx.fillRect(state.x, meter_y, max_meter_width, meter_height);

            // 2.2. 実際のゲージ量を描画
            ctx.fillStyle = 'yellow';
            ctx.fillRect(state.x, meter_y, current_meter_width, meter_height);
        }
        
        // 体力、ゲージ、状態の表示
        ctx.font = "16px Arial";
        ctx.fillStyle = 'black';
        ctx.fillText(`${player}`, info_x, info_y);
        ctx.fillText(`HP: ${state.health} M: ${state.meter.toFixed(0)}`, info_x, info_y + 20);
        ctx.fillText(`State: [${state.state}]`, info_x, info_y + 40);
        
        // キャラクター上に表示されていたテキストは削除 or ゲージ表示に置き換えられたため不要
    }
    
    requestAnimationFrame(gameLoop);
}

document.addEventListener('keydown', (e) => {
    if (gameSection.classList.contains('hidden')) return; // ゲーム中でないなら無視

    let action = null;
    if (e.key === 'ArrowLeft') action = 'move_left';
    else if (e.key === 'ArrowRight') action = 'move_right';
    else if (e.key === ' ') action = 'jump'; 
    // 攻撃キーバインド
    else if (e.key === 'z') action = 'attack_forward'; // zキーを前方攻撃とする
    else if (e.key === 'x') action = 'attack_up';      // xキーを上攻撃とする
    else if (e.key === 's' || e.key === 'ArrowDown') action = 'attack_down'; // Sキーまたは↓で下攻撃
    else if (e.key === 'c') action = 'attack_super';   // cキーを必殺技とする
    // 移動キーの処理で is_moving を true に設定
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        is_moving = true;
    }

    if (action) {
        const input_message = {
            action: action,
            frame: GAME_FRAME,
            user_id: CURRENT_USER_ID
        };
        // サーバーへ自分の入力情報を送信
        WEBSOCKET.send(JSON.stringify(input_message)); 

        // 入力予測: 自分の画面ではすぐに動かす
        // 削除: クライアント側の予測ロジック（applyInput）はサーバー権威モデルでは不正確になるため、削除またはコメントアウト
        // applyInput(CURRENT_USER_ID, input_message); 
    }
});

// ★★★ KEYUP (キーを離したとき) の処理 ★★★
document.addEventListener('keyup', (e) => {
    if (gameSection.classList.contains('hidden')) return;

    if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && is_moving) {
        const stop_message = {
            action: 'stop_move',
            frame: GAME_FRAME,
            user_id: CURRENT_USER_ID
        };
        // サーバーに移動を停止したことを通知
        WEBSOCKET.send(JSON.stringify(stop_message));
        is_moving = false;
    }
});

// リモート/ローカルの入力をゲーム状態に適用する
function applyInput(user_id, input_data) {
    const player = GAME_STATE[user_id];
    if (!player) return;

    // 簡易的な移動ロジック
    if (input_data.action === 'move_left') player.x -= 5;
    if (input_data.action === 'move_right') player.x += 5;
    if (input_data.action === 'attack_punch') {
        // 攻撃処理（ここではダメージ計算をスキップ）
    }
}

function handleRemoteInput(input_data) {
    // サーバーからのリモート入力を受信したら適用
    applyInput(input_data.user_id, input_data);
    
    // ロールバックなどの高度な同期技術はここでは省略
}