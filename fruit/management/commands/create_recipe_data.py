from django.core.management.base import BaseCommand
from fruit.models import Recipe, Ingredient, RecipeIngredient

class Command(BaseCommand):
    help = '创建示例菜谱数据'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始创建示例菜谱数据...')
        
        # 清除现有数据
        Recipe.objects.all().delete()
        Ingredient.objects.all().delete()
        
        # 创建食材
        ingredients = {
            '鸡蛋': Ingredient.objects.create(name='鸡蛋'),
            '番茄': Ingredient.objects.create(name='番茄'),
            '青椒': Ingredient.objects.create(name='青椒'),
            '洋葱': Ingredient.objects.create(name='洋葱'),
            '葱花': Ingredient.objects.create(name='葱花'),
            '盐': Ingredient.objects.create(name='盐'),
            '糖': Ingredient.objects.create(name='糖'),
            '食用油': Ingredient.objects.create(name='食用油'),
            '生抽': Ingredient.objects.create(name='生抽'),
            '五花肉': Ingredient.objects.create(name='五花肉'),
            '冰糖': Ingredient.objects.create(name='冰糖'),
            '老抽': Ingredient.objects.create(name='老抽'),
            '料酒': Ingredient.objects.create(name='料酒'),
            '鸡胸肉': Ingredient.objects.create(name='鸡胸肉'),
            '花生米': Ingredient.objects.create(name='花生米'),
            '干辣椒': Ingredient.objects.create(name='干辣椒'),
            '葱': Ingredient.objects.create(name='葱'),
            '宫保酱汁': Ingredient.objects.create(name='宫保酱汁'),
            '西兰花': Ingredient.objects.create(name='西兰花'),
            '蒜': Ingredient.objects.create(name='蒜'),
            '鸡精': Ingredient.objects.create(name='鸡精'),
        }
        
        # 创建菜谱：番茄炒蛋
        fanqie_chaodan = Recipe.objects.create(
            title='番茄炒蛋',
            cooking_time=15,
            difficulty='简单',
            image_url='/static/fruit/images/recipes/fanqiedan.jpeg',
            steps='1. 将鸡蛋打散，加入少许盐搅拌均匀\n'
                  '2. 番茄洗净切块\n'
                  '3. 热锅倒油，倒入蛋液炒至金黄盛出\n'
                  '4. 锅中再加少许油，倒入番茄翻炒\n'
                  '5. 加入少量盐和糖调味\n'
                  '6. 待番茄出汁变软后，倒入炒好的鸡蛋\n'
                  '7. 翻炒均匀即可出锅',
            is_popular=True
        )
        
        # 添加食材到番茄炒蛋
        RecipeIngredient.objects.create(recipe=fanqie_chaodan, ingredient=ingredients['鸡蛋'], amount='3个', is_main=True)
        RecipeIngredient.objects.create(recipe=fanqie_chaodan, ingredient=ingredients['番茄'], amount='2个', is_main=True)
        RecipeIngredient.objects.create(recipe=fanqie_chaodan, ingredient=ingredients['食用油'], amount='适量')
        RecipeIngredient.objects.create(recipe=fanqie_chaodan, ingredient=ingredients['盐'], amount='适量')
        RecipeIngredient.objects.create(recipe=fanqie_chaodan, ingredient=ingredients['糖'], amount='少许')
        
        # 创建菜谱：青椒炒蛋
        qingjiao_chaodan = Recipe.objects.create(
            title='青椒炒蛋',
            cooking_time=20,
            difficulty='简单',
            image_url='/static/fruit/images/recipes/qingjiaodan.jpeg',
            steps='1. 将鸡蛋打散，加入少许盐搅拌均匀\n'
                  '2. 青椒洗净切块\n'
                  '3. 热锅倒油，倒入蛋液炒至金黄盛出\n'
                  '4. 锅中再加少许油，倒入青椒翻炒\n'
                  '5. 加入少量盐和生抽调味\n'
                  '6. 待青椒变软后，倒入炒好的鸡蛋\n'
                  '7. 翻炒均匀即可出锅',
            is_popular=True
        )
        
        # 添加食材到青椒炒蛋
        RecipeIngredient.objects.create(recipe=qingjiao_chaodan, ingredient=ingredients['鸡蛋'], amount='3个', is_main=True)
        RecipeIngredient.objects.create(recipe=qingjiao_chaodan, ingredient=ingredients['青椒'], amount='2个', is_main=True)
        RecipeIngredient.objects.create(recipe=qingjiao_chaodan, ingredient=ingredients['食用油'], amount='适量')
        RecipeIngredient.objects.create(recipe=qingjiao_chaodan, ingredient=ingredients['盐'], amount='适量')
        RecipeIngredient.objects.create(recipe=qingjiao_chaodan, ingredient=ingredients['生抽'], amount='1勺')
        
        # 创建菜谱：番茄青椒蛋花汤
        tang = Recipe.objects.create(
            title='番茄青椒蛋花汤',
            cooking_time=25,
            difficulty='中等',
            image_url='/static/fruit/images/recipes/tang.jpeg',
            steps='1. 番茄洗净切块，青椒洗净切块\n'
                  '2. 锅中加水烧开，放入番茄块\n'
                  '3. 煮至番茄出汁变软，加入青椒\n'
                  '4. 加入盐调味\n'
                  '5. 将鸡蛋打散，在汤快好时沿锅边缓缓倒入，形成蛋花\n'
                  '6. 撒上葱花即可出锅',
            is_healthy=True
        )
        
        # 添加食材到番茄青椒蛋花汤
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['鸡蛋'], amount='2个', is_main=True)
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['番茄'], amount='1个', is_main=True)
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['青椒'], amount='1个', is_main=True)
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['葱花'], amount='少许')
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['食用油'], amount='适量')
        RecipeIngredient.objects.create(recipe=tang, ingredient=ingredients['盐'], amount='适量')
        
        # 创建菜谱：红烧肉
        hongshaorou = Recipe.objects.create(
            title='红烧肉',
            cooking_time=90,
            difficulty='中等',
            image_url='/static/fruit/images/recipes/hsr.jpeg',
            steps='1. 五花肉洗净切成方块\n'
                  '2. 锅中加冷水，放入肉块，焯水去腥\n'
                  '3. 锅中放入冰糖，小火熬至融化成褐色\n'
                  '4. 倒入肉块翻炒，使肉均匀裹上糖色\n'
                  '5. 加入生抽、老抽、料酒\n'
                  '6. 加水没过肉块，大火烧开后转小火\n'
                  '7. 炖煮60分钟，至肉烂汤浓\n'
                  '8. 大火收汁即可出锅',
            is_popular=True
        )
        
        # 添加食材到红烧肉
        RecipeIngredient.objects.create(recipe=hongshaorou, ingredient=ingredients['五花肉'], amount='500g', is_main=True)
        RecipeIngredient.objects.create(recipe=hongshaorou, ingredient=ingredients['冰糖'], amount='30g')
        RecipeIngredient.objects.create(recipe=hongshaorou, ingredient=ingredients['生抽'], amount='2勺')
        RecipeIngredient.objects.create(recipe=hongshaorou, ingredient=ingredients['老抽'], amount='1勺')
        RecipeIngredient.objects.create(recipe=hongshaorou, ingredient=ingredients['料酒'], amount='2勺')
        
        # 创建菜谱：宫保鸡丁
        gongbao_jiding = Recipe.objects.create(
            title='宫保鸡丁',
            cooking_time=30,
            difficulty='中等',
            image_url='/static/fruit/images/recipes/gbjd.jpeg',
            steps='1. 鸡胸肉洗净切丁，用盐和料酒腌制10分钟\n'
                  '2. 花生米炒熟备用\n'
                  '3. 干辣椒切段，葱切段\n'
                  '4. 热锅倒油，爆香干辣椒\n'
                  '5. 放入鸡丁翻炒至变色\n'
                  '6. 加入宫保酱汁和葱段\n'
                  '7. 最后加入花生米翻炒均匀即可出锅',
            is_popular=True
        )
        
        # 添加食材到宫保鸡丁
        RecipeIngredient.objects.create(recipe=gongbao_jiding, ingredient=ingredients['鸡胸肉'], amount='300g', is_main=True)
        RecipeIngredient.objects.create(recipe=gongbao_jiding, ingredient=ingredients['花生米'], amount='50g')
        RecipeIngredient.objects.create(recipe=gongbao_jiding, ingredient=ingredients['干辣椒'], amount='5个')
        RecipeIngredient.objects.create(recipe=gongbao_jiding, ingredient=ingredients['葱'], amount='1根')
        RecipeIngredient.objects.create(recipe=gongbao_jiding, ingredient=ingredients['宫保酱汁'], amount='适量')
        
        # 创建菜谱：清炒西兰花
        xilanhua = Recipe.objects.create(
            title='清炒西兰花',
            cooking_time=15,
            difficulty='简单',
            image_url='/static/fruit/images/recipes/xlh.jpeg',
            steps='1. 西兰花洗净切小朵\n'
                  '2. 蒜切末\n'
                  '3. 锅中加水烧开，放入西兰花焯水30秒\n'
                  '4. 捞出西兰花，过冷水沥干\n'
                  '5. 热锅倒油，爆香蒜末\n'
                  '6. 放入西兰花翻炒\n'
                  '7. 加入盐和鸡精调味\n'
                  '8. 翻炒均匀即可出锅',
            is_healthy=True
        )
        
        # 添加食材到清炒西兰花
        RecipeIngredient.objects.create(recipe=xilanhua, ingredient=ingredients['西兰花'], amount='1颗', is_main=True)
        RecipeIngredient.objects.create(recipe=xilanhua, ingredient=ingredients['蒜'], amount='3瓣')
        RecipeIngredient.objects.create(recipe=xilanhua, ingredient=ingredients['盐'], amount='适量')
        RecipeIngredient.objects.create(recipe=xilanhua, ingredient=ingredients['食用油'], amount='适量')
        RecipeIngredient.objects.create(recipe=xilanhua, ingredient=ingredients['鸡精'], amount='少许')
        
        self.stdout.write(self.style.SUCCESS('示例菜谱数据创建成功！')) 