# 食刻即选应用软件 V1.0 - 源代码（后30页）

---

## 第31-40页：后端服务 - 收藏与饮食计划

```python
// 代码文件: server/services/favorite_service.py

from datetime import datetime
from sqlalchemy import desc

from models import db, Favorite, Recipe
from utils.cache import cache

class FavoriteService:
    """收藏服务类"""
    
    def get_favorites(self, user_id, page=1, page_size=10):
        """获取用户收藏列表"""
        offset = (page - 1) * page_size
        
        favorites = db.session.query(Favorite, Recipe)\
            .join(Recipe, Favorite.recipe_id == Recipe.id)\
            .filter(Favorite.user_id == user_id)\
            .order_by(desc(Favorite.created_at))\
            .offset(offset).limit(page_size).all()
        
        total = Favorite.query.filter_by(user_id=user_id).count()
        
        result = []
        for fav, recipe in favorites:
            recipe_data = recipe.to_dict()
            recipe_data['favorited_at'] = fav.created_at.strftime('%Y-%m-%d %H:%M:%S')
            result.append(recipe_data)
        
        return {
            'list': result,
            'page': page,
            'pageSize': page_size,
            'hasMore': total > page * page_size
        }
    
    def add_favorite(self, user_id, recipe_id):
        """添加收藏"""
        existing = Favorite.query.filter_by(
            user_id=user_id,
            recipe_id=recipe_id
        ).first()
        
        if existing:
            return {'success': False, 'message': '已收藏'}
        
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return {'success': False, 'message': '菜谱不存在'}
        
        favorite = Favorite(
            user_id=user_id,
            recipe_id=recipe_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(favorite)
        
        recipe.collect_count += 1
        
        db.session.commit()
        
        cache.delete(f'user_favorites:{user_id}')
        
        return {'success': True, 'favorite_id': favorite.id}
    
    def remove_favorite(self, user_id, recipe_id):
        """取消收藏"""
        favorite = Favorite.query.filter_by(
            user_id=user_id,
            recipe_id=recipe_id
        ).first()
        
        if not favorite:
            return {'success': False, 'message': '未收藏'}
        
        db.session.delete(favorite)
        
        recipe = Recipe.query.get(recipe_id)
        if recipe and recipe.collect_count > 0:
            recipe.collect_count -= 1
        
        db.session.commit()
        
        cache.delete(f'user_favorites:{user_id}')
        
        return {'success': True}
    
    def check_favorite(self, user_id, recipe_id):
        """检查是否已收藏"""
        favorite = Favorite.query.filter_by(
            user_id=user_id,
            recipe_id=recipe_id
        ).first()
        
        return {'is_favorite': favorite is not None}
```

```python
// 代码文件: server/services/meal_plan_service.py

from datetime import datetime, timedelta, date
from sqlalchemy import and_
import json

from models import db, MealPlan, Recipe, User
from services.recommendation_service import RecommendationService

class MealPlanService:
    """饮食计划服务类"""
    
    def __init__(self):
        self.recommendation_service = RecommendationService()
    
    def get_meal_plan(self, user_id, plan_date):
        """获取指定日期的饮食计划"""
        meal_plan = MealPlan.query.filter_by(
            user_id=user_id,
            plan_date=plan_date
        ).first()
        
        if not meal_plan:
            return None
        
        result = meal_plan.to_dict()
        
        meals = result.get('meals', {})
        for meal_type, recipes in meals.items():
            detailed_recipes = []
            for recipe_info in recipes:
                recipe = Recipe.query.get(recipe_info.get('recipe_id'))
                if recipe:
                    recipe_data = recipe.to_dict()
                    recipe_data['planned_time'] = recipe_info.get('planned_time')
                    detailed_recipes.append(recipe_data)
            result['meals'][meal_type] = detailed_recipes
        
        return result
    
    def generate_meal_plan(self, user_id, start_date, days=7):
        """生成智能饮食计划"""
        user = User.query.get(user_id)
        if not user:
            return {'error': '用户不存在'}
        
        preferences = user.preferences or {}
        dietary_restrictions = preferences.get('dietary_restrictions', [])
        
        for i in range(days):
            plan_date = start_date + timedelta(days=i)
            
            existing = MealPlan.query.filter_by(
                user_id=user_id,
                plan_date=plan_date
            ).first()
            
            if existing:
                continue
            
            daily_meals = self._generate_daily_meals(
                user_id, 
                plan_date,
                dietary_restrictions
            )
            
            nutrition_summary = self._calculate_nutrition(daily_meals)
            
            meal_plan = MealPlan(
                user_id=user_id,
                plan_date=plan_date,
                meals=daily_meals,
                nutrition_summary=nutrition_summary,
                created_at=datetime.utcnow()
            )
            
            db.session.add(meal_plan)
        
        db.session.commit()
        
        return {'success': True, 'generated_days': days}
    
    def _generate_daily_meals(self, user_id, plan_date, restrictions):
        """生成一天的膳食安排"""
        meals = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': []
        }
        
        breakfast_recipes = self._get_suitable_recipes(
            meal_type='breakfast',
            restrictions=restrictions,
            limit=2
        )
        meals['breakfast'] = [
            {'recipe_id': r.id, 'planned_time': '08:00'} 
            for r in breakfast_recipes
        ]
        
        lunch_recipes = self._get_suitable_recipes(
            meal_type='lunch',
            restrictions=restrictions,
            limit=3
        )
        meals['lunch'] = [
            {'recipe_id': r.id, 'planned_time': '12:00'} 
            for r in lunch_recipes
        ]
        
        dinner_recipes = self._get_suitable_recipes(
            meal_type='dinner',
            restrictions=restrictions,
            limit=2
        )
        meals['dinner'] = [
            {'recipe_id': r.id, 'planned_time': '18:30'} 
            for r in dinner_recipes
        ]
        
        return meals
    
    def _get_suitable_recipes(self, meal_type, restrictions, limit):
        """获取适合的菜谱"""
        query = Recipe.query.filter_by(status=1)
        
        if restrictions:
            for restriction in restrictions:
                query = query.filter(~Recipe.tags.contains([restriction]))
        
        if meal_type == 'breakfast':
            query = query.filter(
                Recipe.cook_time <= 15,
                Recipe.difficulty.in_(['easy'])
            )
        elif meal_type == 'lunch':
            query = query.filter(
                Recipe.calories.between(400, 800)
            )
        elif meal_type == 'dinner':
            query = query.filter(
                Recipe.calories.between(300, 600)
            )
        
        return query.order_by(Recipe.collect_count.desc()).limit(limit).all()
    
    def _calculate_nutrition(self, meals):
        """计算营养汇总"""
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        
        for meal_type, recipes in meals.items():
            for recipe_info in recipes:
                recipe = Recipe.query.get(recipe_info.get('recipe_id'))
                if recipe:
                    total_calories += recipe.calories or 0
                    total_protein += recipe.protein or 0
                    total_fat += recipe.fat or 0
                    total_carbs += recipe.carbs or 0
        
        return {
            'total_calories': total_calories,
            'total_protein': round(total_protein, 2),
            'total_fat': round(total_fat, 2),
            'total_carbs': round(total_carbs, 2),
            'meal_count': sum(len(v) for v in meals.values())
        }
    
    def update_meal_plan(self, user_id, plan_date, meal_type, recipes):
        """更新饮食计划"""
        meal_plan = MealPlan.query.filter_by(
            user_id=user_id,
            plan_date=plan_date
        ).first()
        
        if not meal_plan:
            return {'error': '计划不存在'}
        
        meals = meal_plan.meals or {}
        meals[meal_type] = recipes
        
        meal_plan.meals = meals
        meal_plan.nutrition_summary = self._calculate_nutrition(meals)
        meal_plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {'success': True}
    
    def get_nutrition_analysis(self, user_id, start_date, end_date):
        """获取营养分析报告"""
        plans = MealPlan.query.filter(
            and_(
                MealPlan.user_id == user_id,
                MealPlan.plan_date >= start_date,
                MealPlan.plan_date <= end_date
            )
        ).all()
        
        if not plans:
            return None
        
        total_days = len(plans)
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0
        }
        
        for plan in plans:
            summary = plan.nutrition_summary or {}
            total_nutrition['calories'] += summary.get('total_calories', 0)
            total_nutrition['protein'] += summary.get('total_protein', 0)
            total_nutrition['fat'] += summary.get('total_fat', 0)
            total_nutrition['carbs'] += summary.get('total_carbs', 0)
        
        avg_nutrition = {
            k: round(v / total_days, 2) for k, v in total_nutrition.items()
        }
        
        suggestions = self._generate_nutrition_suggestions(avg_nutrition)
        
        return {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_days': total_days,
            'average_daily': avg_nutrition,
            'suggestions': suggestions
        }
    
    def _generate_nutrition_suggestions(self, avg_nutrition):
        """生成营养建议"""
        suggestions = []
        
        calories = avg_nutrition.get('calories', 0)
        protein = avg_nutrition.get('protein', 0)
        
        if calories < 1500:
            suggestions.append('日均热量摄入偏低，建议适当增加主食摄入')
        elif calories > 2500:
            suggestions.append('日均热量摄入偏高，建议控制油脂和糖分摄入')
        
        if protein < 50:
            suggestions.append('蛋白质摄入不足，建议增加肉类、蛋类或豆制品')
        
        if not suggestions:
            suggestions.append('您的饮食结构较为均衡，请继续保持')
        
        return suggestions
```

```python
// 代码文件: server/utils/auth.py

import jwt
import requests
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta

def verify_wechat_code(code):
    """验证微信登录code，获取openid"""
    appid = current_app.config['WECHAT_APPID']
    secret = current_app.config['WECHAT_SECRET']
    
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {
        'appid': appid,
        'secret': secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'openid' in data:
            return {
                'openid': data['openid'],
                'session_key': data.get('session_key'),
                'unionid': data.get('unionid')
            }
        else:
            return None
    except Exception as e:
        current_app.logger.error(f'微信登录验证失败: {str(e)}')
        return None

def generate_token(user_id, expires_days=30):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=expires_days),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def decode_token(token):
    """解码JWT令牌"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': '缺少认证信息'}), 401
        
        parts = auth_header.split()
        
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({'error': '认证格式错误'}), 401
        
        token = parts[1]
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': '令牌无效或已过期'}), 401
        
        request.user_id = payload['user_id']
        
        return f(*args, **kwargs)
    
    return decorated_function
```

---

## 第41-50页：前端页面 - 菜谱详情与收藏

```javascript
// 代码文件: pages/recipe/detail/detail.js

const app = getApp();
const api = require('../../../config/api.js');

Page({
  data: {
    recipeId: null,
    recipeDetail: null,
    isFavorite: false,
    similarRecipes: [],
    isLoading: true,
    showShareModal: false
  },

  onLoad: function(options) {
    const recipeId = options.id;
    this.setData({ recipeId: recipeId });
    this.loadRecipeDetail(recipeId);
    this.checkFavorite(recipeId);
    this.loadSimilarRecipes(recipeId);
    this.recordView(recipeId);
  },

  onShareAppMessage: function() {
    const recipe = this.data.recipeDetail;
    return {
      title: recipe ? recipe.name : '食刻即选',
      path: '/pages/recipe/detail/detail?id=' + this.data.recipeId,
      imageUrl: recipe ? recipe.coverImage : '/images/share.png'
    };
  },

  loadRecipeDetail: function(recipeId) {
    wx.request({
      url: api.getRecipeDetail + recipeId,
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({
            recipeDetail: res.data.data,
            isLoading: false
          });
        }
      },
      fail: () => {
        wx.showToast({
          title: '加载失败',
          icon: 'none'
        });
      }
    });
  },

  checkFavorite: function(recipeId) {
    wx.request({
      url: api.getFavorites + '/check',
      method: 'GET',
      data: { recipeId: recipeId },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({ isFavorite: res.data.is_favorite });
        }
      }
    });
  },

  toggleFavorite: function() {
    const recipeId = this.data.recipeId;
    const isFavorite = this.data.isFavorite;
    
    if (isFavorite) {
      this.removeFavorite(recipeId);
    } else {
      this.addFavorite(recipeId);
    }
  },

  addFavorite: function(recipeId) {
    wx.request({
      url: api.addFavorite,
      method: 'POST',
      data: { recipeId: recipeId },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          this.setData({ isFavorite: true });
          wx.showToast({
            title: '收藏成功',
            icon: 'success'
          });
        }
      }
    });
  },

  removeFavorite: function(recipeId) {
    wx.request({
      url: api.removeFavorite + recipeId,
      method: 'DELETE',
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          this.setData({ isFavorite: false });
          wx.showToast({
            title: '取消收藏',
            icon: 'none'
          });
        }
      }
    });
  },

  loadSimilarRecipes: function(recipeId) {
    wx.request({
      url: api.getSimilarRecipes,
      method: 'GET',
      data: { recipeId: recipeId, limit: 4 },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({ similarRecipes: res.data.data });
        }
      }
    });
  },

  recordView: function(recipeId) {
    wx.request({
      url: api.recordBehavior,
      method: 'POST',
      data: {
        type: 'view',
        recipeId: recipeId,
        metadata: { timestamp: new Date().toISOString() }
      },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      }
    });
  },

  goToSimilar: function(e) {
    const recipeId = e.currentTarget.dataset.id;
    wx.redirectTo({
      url: '/pages/recipe/detail/detail?id=' + recipeId
    });
  },

  showShare: function() {
    this.setData({ showShareModal: true });
  },

  hideShare: function() {
    this.setData({ showShareModal: false });
  },

  onImagePreview: function(e) {
    const urls = e.currentTarget.dataset.urls;
    const current = e.currentTarget.dataset.current;
    wx.previewImage({
      urls: urls,
      current: current
    });
  }
});
```

```javascript
// 代码文件: pages/favorites/favorites.js

const app = getApp();
const api = require('../../config/api.js');

Page({
  data: {
    favorites: [],
    isLoading: true,
    hasMore: true,
    page: 1,
    pageSize: 10,
    isEditing: false,
    selectedIds: []
  },

  onLoad: function() {
    this.loadFavorites();
  },

  onShow: function() {
    if (!this.data.isLoading) {
      this.setData({ page: 1, favorites: [] });
      this.loadFavorites();
    }
  },

  onPullDownRefresh: function() {
    this.setData({ page: 1, favorites: [], hasMore: true });
    this.loadFavorites();
    wx.stopPullDownRefresh();
  },

  onReachBottom: function() {
    if (this.data.hasMore && !this.data.isLoading) {
      this.loadMoreFavorites();
    }
  },

  loadFavorites: function() {
    this.setData({ isLoading: true });
    
    wx.request({
      url: api.getFavorites,
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
          const data = res.data.data;
          this.setData({
            favorites: data.list,
            hasMore: data.hasMore,
            isLoading: false
          });
        }
      },
      fail: () => {
        this.setData({ isLoading: false });
        wx.showToast({
          title: '加载失败',
          icon: 'none'
        });
      }
    });
  },

  loadMoreFavorites: function() {
    const nextPage = this.data.page + 1;
    this.setData({ isLoading: true });
    
    wx.request({
      url: api.getFavorites,
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
          const data = res.data.data;
          this.setData({
            favorites: this.data.favorites.concat(data.list),
            page: nextPage,
            hasMore: data.hasMore,
            isLoading: false
          });
        }
      }
    });
  },

  goToDetail: function(e) {
    const recipeId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/recipe/detail/detail?id=' + recipeId
    });
  },

  toggleEdit: function() {
    this.setData({
      isEditing: !this.data.isEditing,
      selectedIds: []
    });
  },

  selectItem: function(e) {
    const id = e.currentTarget.dataset.id;
    const selectedIds = this.data.selectedIds;
    
    if (selectedIds.includes(id)) {
      this.setData({
        selectedIds: selectedIds.filter(i => i !== id)
      });
    } else {
      this.setData({
        selectedIds: [...selectedIds, id]
      });
    }
  },

  selectAll: function() {
    const allIds = this.data.favorites.map(f => f.id);
    this.setData({ selectedIds: allIds });
  },

  deleteSelected: function() {
    const selectedIds = this.data.selectedIds;
    if (selectedIds.length === 0) {
      wx.showToast({
        title: '请先选择',
        icon: 'none'
      });
      return;
    }
    
    wx.showModal({
      title: '确认删除',
      content: `确定要删除选中的${selectedIds.length}个收藏吗？`,
      success: (res) => {
        if (res.confirm) {
          this.batchDelete(selectedIds);
        }
      }
    });
  },

  batchDelete: function(ids) {
    let completed = 0;
    
    ids.forEach(id => {
      wx.request({
        url: api.removeFavorite + id,
        method: 'DELETE',
        header: {
          'Authorization': 'Bearer ' + app.globalData.token
        },
        success: () => {
          completed++;
          if (completed === ids.length) {
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
            this.setData({
              isEditing: false,
              selectedIds: [],
              page: 1,
              favorites: []
            });
            this.loadFavorites();
          }
        }
      });
    });
  }
});
```

```javascript
// 代码文件: pages/meal-plan/meal-plan.js

const app = getApp();
const api = require('../../config/api.js');

Page({
  data: {
    currentDate: new Date(),
    weekDates: [],
    selectedDate: null,
    mealPlan: null,
    nutritionSummary: null,
    isLoading: true,
    showGenerator: false
  },

  onLoad: function() {
    this.initWeekDates();
    this.setData({ selectedDate: this.formatDate(new Date()) });
    this.loadMealPlan();
  },

  onShow: function() {
    this.loadMealPlan();
  },

  initWeekDates: function() {
    const dates = [];
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay() + 1);
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      dates.push({
        date: this.formatDate(date),
        day: date.getDate(),
        weekDay: ['一', '二', '三', '四', '五', '六', '日'][i],
        isToday: this.formatDate(date) === this.formatDate(today)
      });
    }
    
    this.setData({ weekDates: dates });
  },

  formatDate: function(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  selectDate: function(e) {
    const date = e.currentTarget.dataset.date;
    this.setData({ selectedDate: date, isLoading: true });
    this.loadMealPlan();
  },

  loadMealPlan: function() {
    wx.request({
      url: api.getMealPlan,
      method: 'GET',
      data: { date: this.data.selectedDate },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const data = res.data.data;
          this.setData({
            mealPlan: data,
            nutritionSummary: data ? data.nutrition_summary : null,
            isLoading: false
          });
        } else if (res.statusCode === 404) {
          this.setData({
            mealPlan: null,
            nutritionSummary: null,
            isLoading: false
          });
        }
      }
    });
  },

  showGeneratorModal: function() {
    this.setData({ showGenerator: true });
  },

  hideGeneratorModal: function() {
    this.setData({ showGenerator: false });
  },

  generatePlan: function() {
    wx.showLoading({ title: '生成中...' });
    
    wx.request({
      url: api.generateMealPlan,
      method: 'POST',
      data: {
        startDate: this.data.selectedDate,
        days: 7
      },
      header: {
        'Authorization': 'Bearer ' + app.globalData.token
      },
      success: (res) => {
        wx.hideLoading();
        if (res.statusCode === 200) {
          wx.showToast({
            title: '生成成功',
            icon: 'success'
          });
          this.setData({ showGenerator: false });
          this.loadMealPlan();
        }
      },
      fail: () => {
        wx.hideLoading();
        wx.showToast({
          title: '生成失败',
          icon: 'none'
        });
      }
    });
  },

  goToDetail: function(e) {
    const recipeId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/recipe/detail/detail?id=' + recipeId
    });
  },

  viewNutrition: function() {
    const startDate = this.data.weekDates[0].date;
    const endDate = this.data.weekDates[6].date;
    
    wx.navigateTo({
      url: '/pages/meal-plan/nutrition/nutrition?start=' + startDate + '&end=' + endDate
    });
  }
});
```

---

## 第51-60页：工具类与配置文件

```javascript
// 代码文件: utils/util.js

const formatTime = date => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  const second = date.getSeconds();

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`;
};

const formatNumber = n => {
  n = n.toString();
  return n[1] ? n : `0${n}`;
};

const formatDate = date => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${year}-${formatNumber(month)}-${formatNumber(day)}`;
};

const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

const showError = (message) => {
  wx.showToast({
    title: message || '操作失败',
    icon: 'none',
    duration: 2000
  });
};

const showSuccess = (message) => {
  wx.showToast({
    title: message || '操作成功',
    icon: 'success',
    duration: 1500
  });
};

const checkNetwork = () => {
  return new Promise((resolve, reject) => {
    wx.getNetworkType({
      success: (res) => {
        if (res.networkType === 'none') {
          showError('请检查网络连接');
          reject(new Error('no network'));
        } else {
          resolve(res.networkType);
        }
      }
    });
  });
};

module.exports = {
  formatTime,
  formatDate,
  formatNumber,
  debounce,
  throttle,
  showError,
  showSuccess,
  checkNetwork
};
```

```python
// 代码文件: server/utils/cache.py

import redis
import json
import pickle
from functools import wraps
from flask import current_app

class Cache:
    """缓存工具类"""
    
    def __init__(self):
        self._redis = None
    
    @property
    def redis(self):
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    current_app.config['REDIS_URL'],
                    decode_responses=False
                )
            except Exception as e:
                current_app.logger.error(f'Redis连接失败: {str(e)}')
                self._redis = None
        return self._redis
    
    def get(self, key):
        """获取缓存"""
        if not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            current_app.logger.error(f'缓存获取失败: {str(e)}')
            return None
    
    def set(self, key, value, timeout=None):
        """设置缓存"""
        if not self.redis:
            return False
        
        try:
            serialized = pickle.dumps(value)
            if timeout:
                self.redis.setex(key, timeout, serialized)
            else:
                self.redis.set(key, serialized)
            return True
        except Exception as e:
            current_app.logger.error(f'缓存设置失败: {str(e)}')
            return False
    
    def delete(self, key):
        """删除缓存"""
        if not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            current_app.logger.error(f'缓存删除失败: {str(e)}')
            return False
    
    def memoize(self, timeout=300):
        """缓存装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = f"{f.__module__}.{f.__name__}:{str(args)}:{str(kwargs)}"
                
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = f(*args, **kwargs)
                
                self.set(cache_key, result, timeout)
                
                return result
            return decorated_function
        return decorator

cache = Cache()
```

```python
// 代码文件: server/utils/validator.py

import re
from typing import Dict, Any, List, Optional

class Validator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式（中国大陆）"""
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_required(data: Dict[str, Any], fields: List[str]) -> List[str]:
        """验证必填字段"""
        missing = []
        for field in fields:
            if field not in data or data[field] is None or data[field] == '':
                missing.append(field)
        return missing
    
    @staticmethod
    def validate_length(value: str, min_len: int = 0, max_len: int = 1000) -> bool:
        """验证字符串长度"""
        return min_len <= len(value) <= max_len
    
    @staticmethod
    def validate_number(value: Any, min_val: Optional[float] = None, 
                        max_val: Optional[float] = None) -> bool:
        """验证数字范围"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """清理字符串，防止XSS攻击"""
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')
        return value
    
    @staticmethod
    def validate_recipe_data(data: Dict[str, Any]) -> Dict[str, str]:
        """验证菜谱数据"""
        errors = {}
        
        if not data.get('name'):
            errors['name'] = '菜谱名称不能为空'
        elif len(data['name']) > 128:
            errors['name'] = '菜谱名称过长'
        
        if not Validator.validate_number(data.get('cook_time'), 1, 1440):
            errors['cook_time'] = '烹饪时间必须在1-1440分钟之间'
        
        if data.get('calories') and not Validator.validate_number(
            data['calories'], 0, 50000):
            errors['calories'] = '热量数值不合法'
        
        return errors
    
    @staticmethod
    def validate_user_preferences(data: Dict[str, Any]) -> Dict[str, str]:
        """验证用户偏好设置"""
        errors = {}
        
        spice_level = data.get('spice_level')
        if spice_level is not None and not Validator.validate_number(
            spice_level, 0, 5):
            errors['spice_level'] = '辣度级别必须在0-5之间'
        
        difficulty = data.get('difficulty')
        if difficulty and difficulty not in ['easy', 'medium', 'hard']:
            errors['difficulty'] = '难度级别不合法'
        
        return errors
```

```python
// 代码文件: server/models/__init__.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, UserBehavior
from .recipe import Recipe, Category
from .favorite import Favorite
from .meal_plan import MealPlan

__all__ = [
    'db',
    'User',
    'UserBehavior',
    'Recipe',
    'Category',
    'Favorite',
    'MealPlan'
]
```

```python
// 代码文件: server/requirements.txt

Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.2
Flask-CORS==4.0.0
Flask-Migrate==4.0.4

psycopg2-binary==2.9.7
SQLAlchemy==2.0.20

redis==5.0.0

requests==2.31.0

numpy==1.24.3
pandas==2.0.3

python-dotenv==1.0.0
Werkzeug==2.3.7
gunicorn==21.2.0

pytest==7.4.2
pytest-flask==1.2.0
```

```json
// 代码文件: project.config.json

{
  "description": "食刻即选项目配置文件",
  "packOptions": {
    "ignore": [],
    "include": []
  },
  "setting": {
    "urlCheck": false,
    "es6": true,
    "enhance": true,
    "postcss": true,
    "preloadBackgroundData": false,
    "minified": true,
    "newFeature": false,
    "coverView": true,
    "nodeModules": false,
    "autoAudits": false,
    "showShadowRootInWxmlPanel": true,
    "scopeDataCheck": false,
    "uglifyFileName": false,
    "checkInvalidKey": true,
    "checkSiteMap": true,
    "uploadWithSourceMap": true,
    "compileHotReLoad": false,
    "lazyloadPlaceholderEnable": false,
    "useMultiFrameRuntime": true,
    "useApiHook": true,
    "useApiHostProcess": true,
    "babelSetting": {
      "ignore": [],
      "disablePlugins": [],
      "outputPath": ""
    },
    "enableEngineNative": false,
    "useIsolateContext": true,
    "userConfirmedBundleSwitch": false,
    "packNpmManually": false,
    "packNpmRelationList": [],
    "minifyWXSS": true,
    "disableUseStrict": false,
    "minifyWXML": true,
    "showES6CompileOption": false,
    "useCompilerPlugins": false
  },
  "compileType": "miniprogram",
  "libVersion": "2.32.0",
  "appid": "wx1234567890abcdef",
  "projectname": "example-app",
  "condition": {}
}
```

```
// 代码文件: README.md

# 食刻即选 - 智能饮食助手

## 项目简介

食刻即选是一款基于微信小程序的智能饮食推荐应用，通过AI算法为用户提供个性化的菜谱推荐和饮食计划。

## 技术架构

- 前端：微信小程序（WXML + WXSS + JavaScript）
- 后端：Python Flask + PostgreSQL
- 缓存：Redis
- 推荐算法：混合推荐策略（内容过滤 + 协同过滤）

## 功能模块

1. 智能推荐系统
2. 用户管理系统
3. 菜谱管理功能
4. 饮食计划管理
5. 收藏和历史记录

## 开发团队

示例科技有限公司

## 版本信息

- 版本号：V1.0
- 开发完成日期：2025-08-25
- 首次发表日期：2025-09-01
```

---

**【后30页源代码结束】**

*注：以上为示例性源代码，展示了小程序前端页面、后端服务、数据库设计和推荐算法的核心实现。实际提交时应根据真实项目代码进行整理。*
