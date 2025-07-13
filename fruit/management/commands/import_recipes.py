import json
import os
from django.core.management.base import BaseCommand
from fruit.models import Recipe, Ingredient, RecipeIngredient

class Command(BaseCommand):
    help = '从JSON文件导入菜谱数据'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始导入菜谱数据...')
        
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        json_file_path = os.path.join(project_root, 'test.json')
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                recipes_data = json.load(file)
                
            # 记录创建的食材，避免重复创建
            ingredients_cache = {}
            
            # 导入每个菜谱
            for recipe_data in recipes_data:
                self.stdout.write(f"导入菜谱: {recipe_data['dish_name']}")
                
                # 提取烹饪时间的数字部分
                cook_time_str = recipe_data.get('cook_time', '30分钟')
                cook_time = int(''.join(filter(str.isdigit, cook_time_str.split('（')[0])))
                
                # 获取营养信息
                nutrition = recipe_data.get('nutrition', {})
                
                # 创建菜谱
                recipe = Recipe.objects.create(
                    title=recipe_data['dish_name'],
                    cooking_time=cook_time,
                    difficulty=recipe_data.get('difficulty', '中等'),
                    image_url=f"/static/fruit/images/recipes/{os.path.basename(recipe_data.get('image_path', ''))}",
                    steps='\n'.join(recipe_data.get('steps', [])),
                    is_popular=True if '热门' in recipe_data.get('description', '') else False,
                    is_healthy=True if '健康' in recipe_data.get('description', '') else False,
                    description=recipe_data.get('description', ''),
                    servings=recipe_data.get('servings', '2-3人份'),
                    calories=recipe_data.get('calories', ''),
                    protein=nutrition.get('protein', ''),
                    fat=nutrition.get('fat', ''),
                    carbohydrates=nutrition.get('carbohydrates', ''),
                    fiber=nutrition.get('fiber', ''),
                    sodium=nutrition.get('sodium', '')
                )
                
                # 添加食材
                for ingredient_data in recipe_data.get('ingredients', []):
                    ingredient_name = ingredient_data['name']
                    
                    # 检查缓存中是否已有该食材
                    if ingredient_name not in ingredients_cache:
                        ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
                        ingredients_cache[ingredient_name] = ingredient
                    else:
                        ingredient = ingredients_cache[ingredient_name]
                    
                    # 创建菜谱食材关联
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=ingredient_data['amount'],
                        is_main=True if recipe_data.get('ingredients', []).index(ingredient_data) < 3 else False
                    )
            
            self.stdout.write(self.style.SUCCESS(f'成功导入 {len(recipes_data)} 个菜谱！'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'找不到文件: {json_file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('JSON文件格式错误'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入过程中发生错误: {str(e)}')) 