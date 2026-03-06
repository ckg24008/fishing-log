# 釣果共有SNSアプリ

## 1. 概要
釣り人が自身の釣果を詳細に記録し、他のユーザーと共有できるSNS機能を備えたWebアプリケーションです。「かゆいところに手が届く」釣り人目線の機能にこだわりました。

## 2. 使用技術
- **バックエンド:** Python, FastAPI, SQLAlchemy
- **フロントエンド:** HTML, CSS, Jinja2テンプレートエンジン
- **データベース:** SQLite
- **バージョン管理:** Git, GitHub

## 3. 機能
- ユーザー登録 / ログイン機能
- 釣果の投稿・編集機能（魚種、サイズ、匹数、天気、タックルデータなど）
- 釣り場の「公開・非公開」選択機能（秘密のポイントを守る機能）
- タイムライン表示（カード型デザイン）
- いいね機能（❤️）
- コメント機能

## 4. ER図

<pre><code>```mermaid
erDiagram
USERS ||--o{ POSTS : "投稿する"
USERS ||--o{ LIKES : "いいねする"
USERS ||--o{ COMMENTS : "コメントする"
POSTS ||--o{ LIKES : "される"
POSTS ||--o{ COMMENTS : "される"

USERS {
    int id PK
    string email
    string nickname
}
POSTS {
    int id PK
    string fish_name
    int size_cm
    int owner_id FK
}
LIKES {
    int id PK
    int user_id FK
    int post_id FK
}
COMMENTS {
    int id PK
    string content
    int user_id FK
    int post_id FK
}
```

## 5. 画面イメージ
<img width="930" height="818" alt="スクリーンショット 2026-03-06 110942" src="https://github.com/user-attachments/assets/d7d6507d-dc5a-4c50-8772-6d5adfbaad31" />
<img width="933" height="825" alt="スクリーンショット 2026-03-06 120129" src="https://github.com/user-attachments/assets/d188cbd2-f831-4ac7-860c-1ddb96205940" />
<img width="931" height="820" alt="スクリーンショット 2026-03-06 120353" src="https://github.com/user-attachments/assets/b2e1a507-cb0f-4c9b-87e9-d2a7cf5ed17e" />
<img width="926" height="818" alt="スクリーンショット 2026-03-06 120415" src="https://github.com/user-attachments/assets/5b8462ad-2058-48f8-8681-72b3f0b4e420" />
<img width="929" height="823" alt="スクリーンショット 2026-03-06 120604" src="https://github.com/user-attachments/assets/f439c2e8-8bcb-4ecc-8e11-6f1da7654f82" />



## 6. 工夫した点
- 釣り人特有の「場所は秘密にしたいが、自慢のタックル（道具）は見せたい」というニーズに応えるため、項目ごとに細かく公開設定ができるように設計しました。
- タイムラインは見やすさを重視し、SNSで主流の「カード型デザイン」を採用しました。
- いいね機能やコメント機能を実装し、単なる記録帳ではなく「コミュニティ」として機能するよう工夫しました。
