from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float # Floatを追加
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# ユーザーテーブル
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    nickname = Column(String)

    # ★復活: マイセット（タックル情報）
    tackle_1 = Column(Text, nullable=True)
    tackle_2 = Column(Text, nullable=True)
    tackle_3 = Column(Text, nullable=True)

    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")

# 投稿テーブル (変更なし)
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    image_url = Column(Text)
    fish_name = Column(String, index=True)
    size_cm = Column(Float) # IntegerからFloatに変更(小数を扱うため)
    quantity = Column(Integer, default=1)
    
    place = Column(String, index=True)
    is_place_public = Column(Boolean, default=True)
    
    weather = Column(String)
    caught_at = Column(DateTime, default=datetime.now)
    
    tackle_text = Column(Text, nullable=True)
    memo = Column(Text, nullable=True)
    is_tackle_public = Column(Boolean, default=True)
    
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="posts")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))

    # 誰がいいねしたか、どの投稿へのいいねかを繋ぐ設定
    user = relationship("User", backref="likes")
    post = relationship("Post", backref="likes")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False) # コメントの内容
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow) # コメントした時間

    # 誰がコメントしたか、どの投稿へのコメントかを繋ぐ設定
    user = relationship("User", backref="comments")
    post = relationship("Post", backref="comments")