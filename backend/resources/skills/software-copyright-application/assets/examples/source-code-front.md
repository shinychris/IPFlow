# 食刻即选应用软件 V1.0 - 源代码（前30页）

> 说明：以下为示例性质的源代码结构，实际应根据真实项目代码整理

---

## 页眉格式示例

```
食刻即选应用软件 V1.0                                        1
```

---

## 第1-5页：项目配置与入口

```javascript
// ============================================================
// File: app.js
// ============================================================

// 食刻即选 - 小程序主入口文件
const utils = require('./utils/util.js');
const api = require('./config/api.js');

App({
  globalData: {
    userInfo: null,
    openid: null,
    token: null,
    userPreferences: {
      cuisine: [],
      spiceLevel: 2,
      difficulty: 'medium',
      dietaryRestrictions: []
    }
  },

  onLaunch: function() {
    console.log('食刻即选小程序启动');
    this.checkUpdate();
    this.initUserData();
  },

  onShow: function(options) {
    console.log('小程序显示', options);
  },

  checkUpdate: function() {
    const updateManager = wx.getUpdateManager();
    updateManager.onCheckForUpdate(function(res) {
      console.log('检查更新结果:', res.hasUpdate);
    });
    updateManager.onUpdateReady(function() {
      wx.showModal({
        title: '更新提示',
        content: '新版本已准备好，是否重启应用？',
        success: function(res) {
          if (res.confirm) {
            updateManager.applyUpdate();
          }
        }
      });
    });
  },

  initUserData: function() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      this.getUserInfo();
    }
  },

  getUserInfo: function() {
    wx.request({
      url: api.getUserInfo,
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + this.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.globalData.userInfo = res.data;
          this.globalData.userPreferences = res.data.preferences;
        }
      }
    });
  }
});
```

```javascript
// ============================================================
// File: config/api.js
// ============================================================

// API接口配置文件
const baseUrl = 'https://api.example.com/v1';

module.exports = {
  baseUrl: baseUrl,
  
  // 用户相关
  login: baseUrl + '/auth/login',
  getUserInfo: baseUrl + '/user/info',
  updatePreferences: baseUrl + '/user/preferences',
  updateUserInfo: baseUrl + '/user/update',
  
  // 菜谱相关
  getRecipeList: baseUrl + '/recipes',
  getRecipeDetail: baseUrl + '/recipes/',
  searchRecipes: baseUrl + '/recipes/search',
  getCategories: baseUrl + '/recipes/categories',
  
  // 推荐相关
  getRecommendations: baseUrl + '/recommendations',
  getDailyPick: baseUrl + '/recommendations/daily',
  getSimilarRecipes: baseUrl + '/recommendations/similar',
  recordBehavior: baseUrl + '/recommendations/behavior',
  
  // 收藏相关
  getFavorites: baseUrl + '/favorites',
  addFavorite: baseUrl + '/favorites',
  removeFavorite: baseUrl + '/favorites/',
  
  // 饮食计划
  getMealPlan: baseUrl + '/meal-plan',
  generateMealPlan: baseUrl + '/meal-plan/generate',
  updateMealPlan: baseUrl + '/meal-plan/',
  getNutritionAnalysis: baseUrl + '/meal-plan/nutrition',
  
  // 评价反馈
  submitReview: baseUrl + '/reviews',
  getRecipeReviews: baseUrl + '/reviews/'
};
```

```json
// ============================================================
// File: app.json
// ============================================================

{
  "pages": [
    "pages/index/index",
    "pages/recipe/detail/detail",
    "pages/recipe/list/list",
    "pages/search/search",
    "pages/meal-plan/meal-plan",
    "pages/favorites/favorites",
    "pages/profile/profile",
    "pages/profile/settings/settings",
    "pages/profile/preferences/preferences",
    "pages/history/history"
  ],
  "window": {
    "backgroundTextStyle": "dark",
    "navigationBarBackgroundColor": "#FF6B35",
    "navigationBarTitleText": "食刻即选",
    "navigationBarTextStyle": "white",
    "backgroundColor": "#F5F5F5"
  },
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#FF6B35",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "images/home.png",
        "selectedIconPath": "images/home-active.png"
      },
      {
        "pagePath": "pages/meal-plan/meal-plan",
        "text": "计划",
        "iconPath": "images/plan.png",
        "selectedIconPath": "images/plan-active.png"
      },
      {
        "pagePath": "pages/favorites/favorites",
        "text": "收藏",
        "iconPath": "images/fav.png",
        "selectedIconPath": "images/fav-active.png"
      },
      {
        "pagePath": "pages/profile/profile",
        "text": "我的",
        "iconPath": "images/profile.png",
        "selectedIconPath": "images/profile-active.png"
      }
    ]
  },
  "sitemapLocation": "sitemap.json",
  "lazyCodeLoading": "requiredComponents"
}
```

---

## 第6-15页：页面代码 - 首页

```javascript
// ============================================================
// File: pages/index/index.js
// ============================================================

const app = getApp();
const api = require('../../config/api.js');

Page({
  data: {
    userInfo: {},
    dailyPick: null,
    recommendations: [],
    categories: [],
    isLoading: true,
    hasMore: true,
    page: 1,
    pageSize: 10
  },

  onLoad: function(options) {
    this.loadCategories();
    this.loadDailyPick();
    this.loadRecommendations();
  },

  onShow: function() {
    if (app.globalData.userInfo) {
      this.setData({ userInfo: app.globalData.userInfo });
    }
  },

  onPullDownRefresh: function() {
    this.setData({ page: 1, recommendations: [] });
    this.loadDailyPick();
    this.loadRecommendations();
    wx.stopPullDownRefresh();
  },

  onReachBottom: function() {
    if (this.data.hasMore) {
      this.loadMoreRecommendations();
    }
  },

  loadCategories: function() {
    wx.request({
      url: api.getCategories,
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({ categories: res.data.data });
        }
      }
    });
  },

  loadDailyPick: function() {
    wx.request({
      url: api.getDailyPick,
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({ 
            dailyPick: res.data.data,
            isLoading: false 
          });
        }
      }
    });
  },

  loadRecommendations: function() {
    wx.request({
      url: api.getRecommendations,
      method: 'GET',
      data: {
        page: this.data.page,
        pageSize: this.data.pageSize
      },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const newData = res.data.data;
          this.setData({
            recommendations: newData.list,
            hasMore: newData.hasMore,
            isLoading: false
          });
        }
      }
    });
  },

  loadMoreRecommendations: function() {
    const nextPage = this.data.page + 1;
    this.setData({ isLoading: true });
    
    wx.request({
      url: api.getRecommendations,
      method: 'GET',
      data: {
        page: nextPage,
        pageSize: this.data.pageSize
      },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const newData = res.data.data;
          this.setData({
            recommendations: this.data.recommendations.concat(newData.list),
            page: nextPage,
            hasMore: newData.hasMore,
            isLoading: false
          });
        }
      }
    });
  },

  goToSearch: function() {
    wx.navigateTo({
      url: '/pages/search/search'
    });
  },

  goToDetail: function(e) {
    const recipeId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/recipe/detail/detail?id=' + recipeId
    });
  },

  goToCategory: function(e) {
    const categoryId = e.currentTarget.dataset.id;
    const categoryName = e.currentTarget.dataset.name;
    wx.navigateTo({
      url: '/pages/recipe/list/list?category=' + categoryId + '&name=' + categoryName
    });
  },

  onShareAppMessage: function() {
    return {
      title: '食刻即选 - 您的智能饮食助手',
      path: '/pages/index/index',
      imageUrl: '/images/share.png'
    };
  }
});
```

```html
<!-- ============================================================ -->
<!-- File: pages/index/index.wxml -->
<!-- ============================================================ -->

<view class="container">
  <!-- 搜索栏 -->
  <view class="search-bar" bindtap="goToSearch">
    <view class="search-input">
      <image class="search-icon" src="/images/search.png"></image>
      <text class="placeholder">搜索菜谱、食材...</text>
    </view>
  </view>

  <!-- 每日精选 -->
  <view class="daily-pick-section" wx:if="{{dailyPick}}">
    <view class="section-header">
      <text class="section-title">今日精选</text>
      <text class="section-subtitle">为您精心挑选</text>
    </view>
    <view class="daily-pick-card" bindtap="goToDetail" data-id="{{dailyPick.id}}">
      <image class="daily-image" src="{{dailyPick.coverImage}}" mode="aspectFill"></image>
      <view class="daily-info">
        <text class="daily-name">{{dailyPick.name}}</text>
        <text class="daily-desc">{{dailyPick.description}}</text>
        <view class="daily-tags">
          <text class="tag" wx:for="{{dailyPick.tags}}" wx:key="index">{{item}}</text>
        </view>
      </view>
    </view>
  </view>

  <!-- 分类导航 -->
  <view class="category-section">
    <view class="section-header">
      <text class="section-title">菜谱分类</text>
    </view>
    <scroll-view class="category-scroll" scroll-x="true">
      <view class="category-list">
        <view class="category-item" 
              wx:for="{{categories}}" 
              wx:key="id"
              bindtap="goToCategory"
              data-id="{{item.id}}"
              data-name="{{item.name}}">
          <image class="category-icon" src="{{item.icon}}"></image>
          <text class="category-name">{{item.name}}</text>
        </view>
      </view>
    </scroll-view>
  </view>

  <!-- 推荐列表 -->
  <view class="recommend-section">
    <view class="section-header">
      <text class="section-title">智能推荐</text>
      <text class="section-subtitle">根据您的偏好推荐</text>
    </view>
    <view class="recipe-list">
      <view class="recipe-item" 
            wx:for="{{recommendations}}" 
            wx:key="id"
            bindtap="goToDetail"
            data-id="{{item.id}}">
        <image class="recipe-image" src="{{item.coverImage}}" mode="aspectFill"></image>
        <view class="recipe-info">
          <text class="recipe-name">{{item.name}}</text>
          <text class="recipe-brief">{{item.brief}}</text>
          <view class="recipe-meta">
            <text class="meta-item">{{item.cookTime}}分钟</text>
            <text class="meta-item">{{item.difficulty}}</text>
            <text class="meta-item">{{item.calories}}千卡</text>
          </view>
        </view>
      </view>
    </view>
  </view>

  <!-- 加载更多 -->
  <view class="loading-more" wx:if="{{isLoading}}">
    <text>加载中...</text>
  </view>
  <view class="no-more" wx:if="{{!hasMore && recommendations.length > 0}}">
    <text>没有更多了</text>
  </view>
</view>
```

```css
/* ============================================================ */
/* File: pages/index/index.wxss */
/* ============================================================ */

.container {
  background-color: #F5F5F5;
  min-height: 100vh;
}

/* 搜索栏 */
.search-bar {
  padding: 20rpx 30rpx;
  background-color: #FF6B35;
}

.search-input {
  display: flex;
  align-items: center;
  background-color: #FFFFFF;
  border-radius: 32rpx;
  padding: 16rpx 24rpx;
}

.search-icon {
  width: 32rpx;
  height: 32rpx;
  margin-right: 16rpx;
}

.placeholder {
  color: #999999;
  font-size: 28rpx;
}

/* 每日精选 */
.daily-pick-section {
  margin: 20rpx;
  background-color: #FFFFFF;
  border-radius: 16rpx;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: baseline;
  padding: 24rpx 20rpx 16rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333333;
  margin-right: 16rpx;
}

.section-subtitle {
  font-size: 24rpx;
  color: #999999;
}

.daily-pick-card {
  position: relative;
}

.daily-image {
  width: 100%;
  height: 400rpx;
}

.daily-info {
  padding: 20rpx;
}

.daily-name {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 12rpx;
}

.daily-desc {
  font-size: 28rpx;
  color: #666666;
  line-height: 1.5;
}

.daily-tags {
  display: flex;
  flex-wrap: wrap;
  margin-top: 16rpx;
}

.tag {
  background-color: #FFF2ED;
  color: #FF6B35;
  font-size: 24rpx;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  margin-right: 12rpx;
  margin-bottom: 8rpx;
}

/* 分类导航 */
.category-section {
  margin: 20rpx;
  background-color: #FFFFFF;
  border-radius: 16rpx;
}

.category-scroll {
  white-space: nowrap;
}

.category-list {
  display: flex;
  padding: 20rpx;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 40rpx;
}

.category-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  margin-bottom: 12rpx;
}

.category-name {
  font-size: 24rpx;
  color: #666666;
}

/* 推荐列表 */
.recommend-section {
  margin: 20rpx;
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding-bottom: 20rpx;
}

.recipe-list {
  padding: 0 20rpx;
}

.recipe-item {
  display: flex;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #EEEEEE;
}

.recipe-image {
  width: 200rpx;
  height: 150rpx;
  border-radius: 12rpx;
  margin-right: 20rpx;
}

.recipe-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.recipe-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333333;
}

.recipe-brief {
  font-size: 26rpx;
  color: #666666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recipe-meta {
  display: flex;
}

.meta-item {
  font-size: 24rpx;
  color: #999999;
  margin-right: 24rpx;
}

.loading-more, .no-more {
  text-align: center;
  padding: 30rpx;
  color: #999999;
  font-size: 26rpx;
}
```

---

## 第16-25页：后端服务 - 用户与推荐

```python
# ============================================================
# File: server/app.py
# ============================================================

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from datetime import timedelta
import os

from config import Config
from models import db, User, Recipe, Favorite, MealPlan
from services.recommendation_service import RecommendationService
from services.user_service import UserService
from services.recipe_service import RecipeService
from services.meal_plan_service import MealPlanService

app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# 创建数据库表
with app.app_context():
    db.create_all()

# ==================== 认证相关接口 ====================

@app.route('/v1/auth/login', methods=['POST'])
def login():
    """微信小程序登录"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': '缺少code参数'}), 400
    
    try:
        # 调用微信接口获取openid
        user_service = UserService()
        result = user_service.wechat_login(code)
        
        # 创建JWT令牌
        access_token = create_access_token(
            identity=result['user_id'],
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'access_token': access_token,
            'user_info': result['user_info'],
            'is_new_user': result['is_new_user']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 用户相关接口 ====================

@app.route('/v1/user/info', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取用户信息"""
    user_id = get_jwt_identity()
    user_service = UserService()
    
    try:
        user_info = user_service.get_user_by_id(user_id)
        return jsonify({'data': user_info}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/user/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """更新用户偏好设置"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user_service = UserService()
    try:
        result = user_service.update_preferences(user_id, data)
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/user/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """获取用户偏好设置"""
    user_id = get_jwt_identity()
    user_service = UserService()
    
    try:
        preferences = user_service.get_preferences(user_id)
        return jsonify({'data': preferences}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 推荐相关接口 ====================

@app.route('/v1/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """获取个性化推荐列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    
    recommendation_service = RecommendationService()
    
    try:
        result = recommendation_service.get_recommendations(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/recommendations/daily', methods=['GET'])
@jwt_required()
def get_daily_pick():
    """获取今日精选"""
    user_id = get_jwt_identity()
    recommendation_service = RecommendationService()
    
    try:
        result = recommendation_service.get_daily_pick(user_id)
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/recommendations/similar', methods=['GET'])
@jwt_required()
def get_similar_recipes():
    """获取相似菜谱推荐"""
    user_id = get_jwt_identity()
    recipe_id = request.args.get('recipeId', type=int)
    limit = request.args.get('limit', 5, type=int)
    
    if not recipe_id:
        return jsonify({'error': '缺少recipeId参数'}), 400
    
    recommendation_service = RecommendationService()
    
    try:
        result = recommendation_service.get_similar_recipes(
            user_id=user_id,
            recipe_id=recipe_id,
            limit=limit
        )
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/recommendations/behavior', methods=['POST'])
@jwt_required()
def record_behavior():
    """记录用户行为"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    recommendation_service = RecommendationService()
    
    try:
        result = recommendation_service.record_behavior(
            user_id=user_id,
            behavior_type=data.get('type'),
            recipe_id=data.get('recipeId'),
            metadata=data.get('metadata', {})
        )
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 菜谱相关接口 ====================

@app.route('/v1/recipes', methods=['GET'])
def get_recipe_list():
    """获取菜谱列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    category = request.args.get('category', type=int)
    
    recipe_service = RecipeService()
    
    try:
        result = recipe_service.get_list(
            page=page,
            page_size=page_size,
            category=category
        )
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """获取菜谱详情"""
    recipe_service = RecipeService()
    
    try:
        result = recipe_service.get_detail(recipe_id)
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/recipes/search', methods=['GET'])
def search_recipes():
    """搜索菜谱"""
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    
    recipe_service = RecipeService()
    
    try:
        result = recipe_service.search(
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        return jsonify({'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

```python
# ============================================================
# File: server/models/user.py
# ============================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    unionid = db.Column(db.String(128), nullable=True)
    nickname = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(256), nullable=True)
    gender = db.Column(db.Integer, default=0)
    country = db.Column(db.String(64), nullable=True)
    province = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    
    # 偏好设置（JSON格式存储）
    preferences = db.Column(db.JSON, default=lambda: {
        'cuisine': [],
        'spice_level': 2,
        'difficulty': 'medium',
        'dietary_restrictions': [],
        'cook_time_preference': 30
    })
    
    # 用户状态
    status = db.Column(db.Integer, default=1)
    is_vip = db.Column(db.Boolean, default=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # 关联关系
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    meal_plans = db.relationship('MealPlan', backref='user', lazy='dynamic')
    behaviors = db.relationship('UserBehavior', backref='user', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'gender': self.gender,
            'preferences': self.preferences,
            'is_vip': self.is_vip,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class UserBehavior(db.Model):
    """用户行为记录模型"""
    __tablename__ = 'user_behaviors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    behavior_type = db.Column(db.String(32), nullable=False)  # view, like, collect, share, cook
    
    # 行为元数据（停留时间、评分等）
    metadata = db.Column(db.JSON, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserBehavior {self.user_id}:{self.behavior_type}:{self.recipe_id}>'
```

---

## 第26-30页：数据库配置与推荐算法

```python
# ============================================================
# File: server/config.py
# ============================================================

import os
from datetime import timedelta

class Config:
    """应用配置类"""
    
    # 密钥配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost:5432/shikejixuan'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800
    }
    
    # Redis配置（缓存）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # 微信小程序配置
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or 'your-app-id'
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET') or 'your-app-secret'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 推荐算法配置
    RECOMMENDATION_CONFIG = {
        'content_weight': 0.4,
        'collaborative_weight': 0.4,
        'popular_weight': 0.2,
        'learning_rate': 0.01
    }
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/shikejixuan_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

```sql
-- ============================================================
-- File: server/migrations/001_initial_schema.sql
-- ============================================================

-- 创建数据库
CREATE DATABASE shikejixuan OWNER postgres ENCODING 'UTF8';

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    openid VARCHAR(128) UNIQUE NOT NULL,
    unionid VARCHAR(128),
    nickname VARCHAR(64),
    avatar_url VARCHAR(256),
    gender INTEGER DEFAULT 0,
    country VARCHAR(64),
    province VARCHAR(64),
    city VARCHAR(64),
    preferences JSONB DEFAULT '{}',
    status INTEGER DEFAULT 1,
    is_vip BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_openid ON users(openid);

-- 菜谱表
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    brief TEXT,
    description TEXT,
    cover_image VARCHAR(256),
    cuisine_type VARCHAR(32),
    difficulty VARCHAR(16),
    cook_time INTEGER,
    calories INTEGER,
    protein DECIMAL(8,2),
    fat DECIMAL(8,2),
    carbs DECIMAL(8,2),
    spice_level INTEGER DEFAULT 0,
    tags JSONB DEFAULT '[]',
    ingredients JSONB DEFAULT '[]',
    steps JSONB DEFAULT '[]',
    nutrition JSONB DEFAULT '{}',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    collect_count INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recipes_cuisine ON recipes(cuisine_type);
CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX idx_recipes_status ON recipes(status);

-- 用户行为表
CREATE TABLE user_behaviors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    behavior_type VARCHAR(32) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_behaviors_user ON user_behaviors(user_id);
CREATE INDEX idx_behaviors_recipe ON user_behaviors(recipe_id);
CREATE INDEX idx_behaviors_type ON user_behaviors(behavior_type);

-- 收藏表
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, recipe_id)
);

CREATE INDEX idx_favorites_user ON favorites(user_id);

-- 饮食计划表
CREATE TABLE meal_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    meals JSONB DEFAULT '{}',
    nutrition_summary JSONB DEFAULT '{}',
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meal_plans_user ON meal_plans(user_id);
CREATE INDEX idx_meal_plans_date ON meal_plans(plan_date);

-- 分类表
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    icon VARCHAR(256),
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认分类
INSERT INTO categories (name, icon, sort_order) VALUES
('家常菜', '/images/cat-home.png', 1),
('川菜', '/images/cat-sichuan.png', 2),
('粤菜', '/images/cat-cantonese.png', 3),
('湘菜', '/images/cat-hunan.png', 4),
('鲁菜', '/images/cat-shandong.png', 5),
('江浙菜', '/images/cat-jiangzhe.png', 6),
('西餐', '/images/cat-western.png', 7),
('烘焙', '/images/cat-baking.png', 8);
```

```python
# ============================================================
# File: server/services/recommendation_service.py
# ============================================================

import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func

from models import db, User, Recipe, UserBehavior, Favorite
from utils.cache import cache

class RecommendationService:
    """推荐服务类 - 实现混合推荐算法"""
    
    def __init__(self):
        self.content_weight = 0.4
        self.collaborative_weight = 0.4
        self.popular_weight = 0.2
    
    @cache.memoize(timeout=3600)
    def get_recommendations(self, user_id, page=1, page_size=10):
        """获取个性化推荐列表"""
        # 获取用户偏好
        user = User.query.get(user_id)
        if not user:
            return self._get_popular_recipes(page, page_size)
        
        preferences = user.preferences or {}
        
        # 三种推荐策略
        content_based = self._content_based_recommend(user_id, preferences, limit=50)
        collaborative = self._collaborative_recommend(user_id, limit=50)
        popular = self._get_popular_recipes(1, 50)['list']
        
        # 混合推荐结果
        merged_scores = defaultdict(float)
        
        # 内容过滤得分
        for i, recipe in enumerate(content_based):
            merged_scores[recipe['id']] += self.content_weight * (1 - i / len(content_based))
        
        # 协同过滤得分
        for i, recipe in enumerate(collaborative):
            merged_scores[recipe['id']] += self.collaborative_weight * (1 - i / len(collaborative))
        
        # 热门得分
        for i, recipe in enumerate(popular):
            merged_scores[recipe['id']] += self.popular_weight * (1 - i / len(popular))
        
        # 去重：排除已浏览和已收藏的菜谱
        viewed_ids = self._get_viewed_recipe_ids(user_id)
        for rid in viewed_ids:
            if rid in merged_scores:
                del merged_scores[rid]
        
        # 按得分排序
        sorted_recipes = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        recipe_ids = [rid for rid, _ in sorted_recipes[start:end]]
        
        # 获取完整菜谱信息
        recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()
        recipe_map = {r.id: r.to_dict() for r in recipes}
        
        result = [recipe_map[rid] for rid in recipe_ids if rid in recipe_map]
        
        return {
            'list': result,
            'page': page,
            'pageSize': page_size,
            'hasMore': len(sorted_recipes) > end
        }
    
    def get_daily_pick(self, user_id):
        """获取今日精选"""
        # 基于用户偏好和时令推荐一道精选菜谱
        user = User.query.get(user_id)
        
        # 查询今日是否已有精选
        today = datetime.now().date()
        cache_key = f'daily_pick:{user_id}:{today}'
        cached = cache.get(cache_key)
        
        if cached:
            recipe = Recipe.query.get(cached)
            if recipe:
                return recipe.to_dict()
        
        # 选择今日精选
        preferences = user.preferences if user else {}
        cuisine_preference = preferences.get('cuisine', [])
        
        query = Recipe.query.filter_by(status=1)
        
        if cuisine_preference:
            query = query.filter(Recipe.cuisine_type.in_(cuisine_preference))
        
        # 综合考虑评分、收藏数、制作次数
        query = query.order_by(
            (Recipe.like_count * 2 + Recipe.collect_count * 3 + Recipe.view_count).desc()
        )
        
        recipe = query.first()
        
        if recipe:
            cache.set(cache_key, recipe.id, timeout=86400)
            return recipe.to_dict()
        
        return None
    
    def _content_based_recommend(self, user_id, preferences, limit=50):
        """基于内容的推荐"""
        query = Recipe.query.filter_by(status=1)
        
        # 根据用户偏好筛选
        cuisine = preferences.get('cuisine', [])
        if cuisine:
            query = query.filter(Recipe.cuisine_type.in_(cuisine))
        
        difficulty = preferences.get('difficulty')
        if difficulty:
            difficulty_map = {
                'easy': ['easy'],
                'medium': ['easy', 'medium'],
                'hard': ['easy', 'medium', 'hard']
            }
            query = query.filter(Recipe.difficulty.in_(difficulty_map.get(difficulty, ['medium'])))
        
        spice_level = preferences.get('spice_level', 2)
        query = query.filter(Recipe.spice_level <= spice_level + 1)
        
        recipes = query.order_by(Recipe.collect_count.desc()).limit(limit).all()
        return [r.to_dict() for r in recipes]
    
    def _collaborative_recommend(self, user_id, limit=50):
        """基于协同过滤的推荐"""
        # 找到相似用户
        similar_users = self._find_similar_users(user_id)
        
        if not similar_users:
            return []
        
        # 获取相似用户喜欢的菜谱
        similar_user_ids = [uid for uid, _ in similar_users]
        
        liked_recipes = db.session.query(UserBehavior.recipe_id, func.count(UserBehavior.id).label('count'))\
            .filter(UserBehavior.user_id.in_(similar_user_ids))\
            .filter(UserBehavior.behavior_type.in_(['like', 'collect']))\
            .group_by(UserBehavior.recipe_id)\
            .order_by(func.count(UserBehavior.id).desc())\
            .limit(limit)\
            .all()
        
        recipe_ids = [r[0] for r in liked_recipes]
        recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()
        
        return [r.to_dict() for r in recipes]
    
    def _find_similar_users(self, user_id, top_n=20):
        """找到与指定用户相似的用户"""
        # 获取用户的偏好和行为
        user_favorites = set(
            f.recipe_id for f in Favorite.query.filter_by(user_id=user_id).all()
        )
        
        if not user_favorites:
            return []
        
        # 找到有相似喜好的用户
        similar_users = db.session.query(
            Favorite.user_id,
            func.count(Favorite.recipe_id).label('common_count')
        ).filter(
            Favorite.recipe_id.in_(user_favorites)
        ).filter(
            Favorite.user_id != user_id
        ).group_by(
            Favorite.user_id
        ).order_by(
            func.count(Favorite.recipe_id).desc()
        ).limit(top_n).all()
        
        return [(uid, count) for uid, count in similar_users]
    
    def _get_popular_recipes(self, page=1, page_size=10):
        """获取热门菜谱"""
        offset = (page - 1) * page_size
        
        recipes = Recipe.query.filter_by(status=1)\
            .order_by(Recipe.view_count.desc(), Recipe.like_count.desc())\
            .offset(offset).limit(page_size).all()
        
        total = Recipe.query.filter_by(status=1).count()
        
        return {
            'list': [r.to_dict() for r in recipes],
            'page': page,
            'pageSize': page_size,
            'hasMore': total > page * page_size
        }
    
    def _get_viewed_recipe_ids(self, user_id):
        """获取用户已浏览的菜谱ID"""
        behaviors = UserBehavior.query.filter_by(
            user_id=user_id,
            behavior_type='view'
        ).all()
        return set(b.recipe_id for b in behaviors)
    
    def record_behavior(self, user_id, behavior_type, recipe_id, metadata=None):
        """记录用户行为"""
        behavior = UserBehavior(
            user_id=user_id,
            recipe_id=recipe_id,
            behavior_type=behavior_type,
            metadata=metadata or {}
        )
        
        db.session.add(behavior)
        
        # 更新菜谱统计
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            if behavior_type == 'view':
                recipe.view_count += 1
            elif behavior_type == 'like':
                recipe.like_count += 1
            elif behavior_type == 'collect':
                recipe.collect_count += 1
        
        db.session.commit()
        
        return {'success': True}
    
    def get_similar_recipes(self, user_id, recipe_id, limit=5):
        """获取相似菜谱"""
        target_recipe = Recipe.query.get(recipe_id)
        
        if not target_recipe:
            return []
        
        # 基于标签、菜系、难度相似度
        query = Recipe.query.filter(
            Recipe.id != recipe_id,
            Recipe.status == 1
        )
        
        # 优先同菜系
        if target_recipe.cuisine_type:
            query = query.filter_by(cuisine_type=target_recipe.cuisine_type)
        
        # 相似难度
        query = query.filter_by(difficulty=target_recipe.difficulty)
        
        recipes = query.order_by(Recipe.collect_count.desc()).limit(limit).all()
        
        return [r.to_dict() for r in recipes]
```

---

**【前30页源代码结束】**

*注：以上为示例性源代码，展示了小程序前端页面、后端服务、数据库设计和推荐算法的核心实现。实际提交时应根据真实项目代码进行整理。*
