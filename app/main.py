import shutil # ファイル操作用
import uuid   # ユニークなファイル名生成用
import os
from datetime import datetime # 日付変換用
from fastapi import FastAPI, Request, Depends, Form, Response, UploadFile, File, HTTPException, status
from fastapi.staticfiles import StaticFiles # 静的ファイル用
from fastapi.responses import HTMLResponse, RedirectResponse # ★RedirectResponseを追加
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
import hashlib # ★ハッシュ化（暗号化）用に追加
from sqlalchemy import func # func を追加（合計値を計算するため）
# or_ を追加（魚種「または」場所で検索するため）
from sqlalchemy import func, or_

from . import models, database

# DBテーブル作成
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# 画像フォルダを公開設定にする（ブラウザから /static/... でアクセスできるようにする）
app.mount("/static", StaticFiles(directory="app/static"), name="static")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# データベース接続用のセッションを作る関数

# トップページ
@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request,
    q: str = None,         # 検索キーワード (query)
    sort: str = "date_desc", # 並び替え順 (デフォルトは日付新しい順)
    db: Session = Depends(database.get_db)
):
    # 1. ログインチェック
    user_id = request.cookies.get("user_id")
    current_user = None
    total_catch = 0

    if user_id:
        current_user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        
        # 総釣果数の計算（ログインユーザー自身の通算記録として残しておく）
        total_catch = db.query(func.sum(models.Post.quantity)).\
            filter(models.Post.user_id == int(user_id)).\
            scalar() or 0

    # --------------------------------------------------
    # ★ここが変更点！「みんなの公開タイムライン」を作る土台
    # --------------------------------------------------
    query = db.query(models.Post).filter(models.Post.is_public == True)

    # ★検索機能 (タイムラインの中からキーワードで絞り込み！)
    if q:
        # 魚種 OR 場所 にキーワードが含まれているか
        query = query.filter(
            or_(
                models.Post.fish_name.contains(q),
                models.Post.place.contains(q),
                models.Post.memo.contains(q) # メモも検索対象に追加
            )
        )

    # ★並び替え機能 (タイムラインを好きな順に並び替え！)
    if sort == "date_desc":
        query = query.order_by(models.Post.caught_at.desc()) # 新しい順
    elif sort == "date_asc":
        query = query.order_by(models.Post.caught_at.asc())  # 古い順
    elif sort == "size_desc":
        query = query.order_by(models.Post.size_cm.desc())   # 大きい順
    elif sort == "size_asc":
        query = query.order_by(models.Post.size_cm.asc())    # 小さい順
    elif sort == "quantity_desc":
        query = query.order_by(models.Post.quantity.desc())  # 数が多い順
    
    # データ取得
    posts = query.all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "みんなの釣果タイムライン", # タイトルも少し変更！
        "user": current_user,
        "posts": posts,
        "total_catch": total_catch,
        "q": q,      # 画面に今の検索ワードを戻す
        "sort": sort # 画面に今の並び順を戻す
    })
    
# ① 登録画面を表示する (GET)
@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# ② 登録情報を受け取って保存する (POST)
@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...), 
    nickname: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # 1. すでに同じメアドの人がいないかチェック
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "そのメールアドレスは既に登録されています。"
        })

    # 2. パスワードをハッシュ化（SHA-256）
    # ※授業用なので標準ライブラリを使います
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # 3. ユーザーを作成して保存
    new_user = models.User(email=email, password_hash=hashed_password, nickname=nickname)
    db.add(new_user)
    db.commit()

    # 4. トップページへリダイレクト（移動）
    return RedirectResponse(url="/", status_code=303)

# ③ ログイン画面を表示 (GET)
@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ④ ログイン処理 (POST)
@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # 1. ユーザー検索
    user = db.query(models.User).filter(models.User.email == email).first()

    # 2. ユーザーがいない、またはパスワードが違う場合
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if not user or user.password_hash != hashed_password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "メールアドレスかパスワードが間違っています。"
        })

    # 3. ログイン成功！ -> CookieにIDを保存してトップへ
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id)) # ★ここで会員証発行
    return response

# ⑤ ログアウト処理
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id") # ★会員証を破棄
    return response

# ⑥ 新規投稿画面を表示 (GET)
@app.get("/post/new", response_class=HTMLResponse)
async def new_post_page(request: Request, db: Session = Depends(database.get_db)): # dbを追加
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    # ★追加: ユーザー情報を取得してテンプレートに渡す
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        
    return templates.TemplateResponse("post_new.html", {
        "request": request,
        "user": user # これが必要！
    })

# ⑦ 新規投稿の保存処理 (POST)
@app.post("/post/new")
async def create_post(
    request: Request,
    file: UploadFile = File(...),
    fish_name: str = Form(...),
    size_cm: float = Form(...),
    quantity: int = Form(...),
    place: str = Form(...),
    weather: str = Form(...),
    caught_at: str = Form(...),
    tackle_text: str = Form(""),
    memo: str = Form(""),
    is_place_public: bool = Form(False),
    is_tackle_public: bool = Form(False),
    is_public: bool = Form(False),
    db: Session = Depends(database.get_db)
):
    # 1. ユーザーID取得
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # 2. 画像を保存する
    # ファイル名が被らないようにUUIDを使う
    file_extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    save_path = f"app/static/images/{filename}"
    
    # ファイルを書き込む
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # DBに保存するパス
    image_url = f"/static/images/{filename}"

    # 3. 日付変換
    caught_at_dt = datetime.strptime(caught_at, "%Y-%m-%dT%H:%M")

    # 4. DBに登録
    new_post = models.Post(
        user_id=int(user_id),
        image_url=image_url,
        fish_name=fish_name,
        size_cm=size_cm,
        quantity=quantity,
        place=place,
        is_place_public=is_place_public,
        weather=weather,
        caught_at=caught_at_dt,
        tackle_text=tackle_text,
        memo=memo,
        is_tackle_public=is_tackle_public,
        is_public=is_public
    )
    db.add(new_post)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

# ⑧ 編集画面を表示 (GET)
@app.get("/post/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_page(post_id: int, request: Request, db: Session = Depends(database.get_db)):
    # ログインチェック
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # 該当の投稿データを取得
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    # データがない、または他人の投稿ならエラー（トップへ戻す）
    if not post or post.user_id != int(user_id):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("post_edit.html", {"request": request, "post": post})


# ⑨ 編集内容を保存 (POST)
@app.post("/post/update/{post_id}")
async def update_post(
    post_id: int,
    request: Request,
    # 画像は任意（変更しない場合はNoneになる）
    file: UploadFile = File(None), 
    fish_name: str = Form(...),
    size_cm: float = Form(...),
    quantity: int = Form(...),
    place: str = Form(...),
    weather: str = Form(...),
    caught_at: str = Form(...),
    memo: str = Form(""),
    # チェックボックス
    is_place_public: bool = Form(False),
    is_tackle_public: bool = Form(False),
    is_public: bool = Form(False),
    db: Session = Depends(database.get_db)
):
    # ログインチェック＆データ取得
    user_id = request.cookies.get("user_id")
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post or not user_id or post.user_id != int(user_id):
        return RedirectResponse(url="/", status_code=303)

    # --- 画像の更新処理 ---
    # もし新しい画像がアップロードされていたら差し替える
    if file and file.filename:
        file_extension = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        save_path = f"app/static/images/{filename}"
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # DBのパス情報を更新
        post.image_url = f"/static/images/{filename}"

    # --- データの更新 ---
    post.fish_name = fish_name
    post.size_cm = size_cm
    post.quantity = quantity
    post.place = place
    post.weather = weather
    post.caught_at = datetime.strptime(caught_at, "%Y-%m-%dT%H:%M")
    post.memo = memo
    post.is_place_public = is_place_public
    post.is_tackle_public = is_tackle_public
    post.is_public = is_public

    # DBへ反映
    db.commit()

    # トップページへ戻る
    return RedirectResponse(url="/", status_code=303)

# ⑩ 投稿の削除処理 (POST)
@app.post("/post/delete/{post_id}")
async def delete_post(
    post_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    # 1. ログインチェック
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # 2. 削除対象の投稿を取得
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    # 3. 自分の投稿でなければトップへ戻す（不正防止）
    if not post or post.user_id != int(user_id):
        return RedirectResponse(url="/", status_code=303)

    # 4. 画像ファイルを削除する（ゴミ掃除）
    # 画像パス "/static/images/xxx.jpg" を "app/static/images/xxx.jpg" に変換
    if post.image_url:
        # 先頭の "/" を取って "app" をつける
        file_path = f"app{post.image_url}"
        if os.path.exists(file_path):
            os.remove(file_path)

    # 5. DBから削除
    db.delete(post)
    db.commit()

    # 6. トップへ戻る
    return RedirectResponse(url="/", status_code=303)

# ⑪ マイセット保存処理 (POST) - main.pyの一番下に追加
@app.post("/mypage/tackle")
async def save_tackle(
    request: Request,
    tackle_1: str = Form(None),
    tackle_2: str = Form(None),
    tackle_3: str = Form(None),
    db: Session = Depends(database.get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    
    # データを更新
    user.tackle_1 = tackle_1
    user.tackle_2 = tackle_2
    user.tackle_3 = tackle_3
    db.commit()
    
    # マイページ（後で作る）があればそこへ、なければトップへ
    return RedirectResponse(url="/mypage", status_code=303)

# ---------------------------------------------------------
#  以下、マイページ機能（一番下に追加）
# ---------------------------------------------------------

# マイページを表示
@app.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request, db: Session = Depends(database.get_db)): # ★ Depends(database.get_db) に修正
    # CookieからユーザーIDを取得
    user_id = request.cookies.get("user_id") # ★ session から cookies に修正
    
    # ログインしてなければログイン画面へ
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # ユーザー情報をDBから取得
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    
    # このユーザーの全投稿を取得（日付が新しい順）
    posts = db.query(models.Post).filter(models.Post.user_id == user.id).order_by(models.Post.caught_at.desc()).all()
    
    # 釣った魚の合計数を計算
    total_catch = sum(post.quantity for post in posts)

    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "user": user,
        "posts": posts,
        "total_catch": total_catch
    })

# マイページのタックルデータを保存する処理
@app.post("/mypage/tackle")
async def update_tackle(
    request: Request,
    tackle_1: str = Form(None), 
    tackle_2: str = Form(None),
    tackle_3: str = Form(None),
    db: Session = Depends(database.get_db) # ★ Depends(database.get_db) に修正
):
    # CookieからユーザーIDを取得
    user_id = request.cookies.get("user_id") # ★ session から cookies に修正
    
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    
    # データを上書き保存
    user.tackle_1 = tackle_1
    user.tackle_2 = tackle_2
    user.tackle_3 = tackle_3
    
    db.commit() # 確定！
    
    # 保存したらマイページを表示しなおす
    return RedirectResponse(url="/mypage", status_code=303)