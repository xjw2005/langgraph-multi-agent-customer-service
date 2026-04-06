# 母婴商品数据模型
# 定义高端母婴商品的完整数据结构

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

class ProductCategory(Enum):
    """商品分类枚举"""
    FORMULA = "奶粉"
    DIAPERS = "纸尿裤"
    BABY_FOOD = "辅食"
    CARE_PRODUCTS = "护理用品"
    TOYS = "玩具"
    CLOTHING = "服装"
    FEEDING = "喂养用品"
    SAFETY = "安全用品"
    FURNITURE = "家具用品"

class AgeRange(Enum):
    """适用年龄范围"""
    NEWBORN = "0-3个月"
    INFANT = "3-6个月"
    MOBILE_BABY = "6-12个月"
    TODDLER = "12-24个月"
    PRESCHOOL = "2-5岁"
    ALL_AGES = "全年龄段"

class CertificationType(Enum):
    """认证类型"""
    ORGANIC = "有机认证"
    FDA = "FDA认证"
    EU_STANDARD = "欧盟标准"
    ISO = "ISO认证"
    CHINA_STANDARD = "国标认证"
    HALAL = "清真认证"
    NON_GMO = "非转基因"

@dataclass
class NutritionalInfo:
    """营养成分信息"""
    protein: Optional[float] = None          # 蛋白质含量 (g/100g)
    fat: Optional[float] = None              # 脂肪含量 (g/100g)
    carbohydrate: Optional[float] = None     # 碳水化合物含量 (g/100g)
    dha: Optional[float] = None              # DHA含量 (mg/100g)
    ara: Optional[float] = None              # ARA含量 (mg/100g)
    calcium: Optional[float] = None          # 钙含量 (mg/100g)
    iron: Optional[float] = None             # 铁含量 (mg/100g)
    vitamin_d: Optional[float] = None        # 维生素D含量 (μg/100g)
    probiotics: Optional[str] = None         # 益生菌类型
    additional_nutrients: Dict[str, float] = field(default_factory=dict)

@dataclass
class SafetyInfo:
    """安全信息"""
    allergens: List[str] = field(default_factory=list)      # 过敏原
    warnings: List[str] = field(default_factory=list)       # 安全警告
    age_restrictions: List[str] = field(default_factory=list)  # 年龄限制
    usage_precautions: List[str] = field(default_factory=list)  # 使用注意事项

@dataclass
class BabyProduct:
    """
    高端母婴商品完整数据模型
    """
    # 必需字段（无默认值）
    product_id: str
    name: str
    brand: str
    category: ProductCategory
    price: float
    age_range: AgeRange

    # 可选字段（有默认值）
    sub_category: str = ""
    original_price: Optional[float] = None
    currency: str = "CNY"
    price_per_unit: Optional[str] = None  # 如 "每100g"
    suitable_conditions: List[str] = field(default_factory=list)  # 如["敏感肌肤", "易消化"]
    gender_preference: Optional[str] = None  # "男宝", "女宝", "通用"

    # 产品特性
    premium_features: List[str] = field(default_factory=list)  # 高端特性
    key_ingredients: List[str] = field(default_factory=list)   # 主要成分
    nutritional_info: Optional[NutritionalInfo] = None

    # 认证和质量
    certifications: List[CertificationType] = field(default_factory=list)
    origin_country: str = ""
    manufacturing_date: Optional[str] = None
    shelf_life: Optional[str] = None

    # 安全信息
    safety_info: SafetyInfo = field(default_factory=SafetyInfo)

    # 描述和指导
    description: str = ""
    usage_guide: str = ""
    storage_instructions: str = ""

    # 规格信息
    specifications: Dict[str, Any] = field(default_factory=dict)  # 重量、尺寸等
    package_info: Dict[str, str] = field(default_factory=dict)    # 包装信息

    # 评价和推荐
    expert_rating: Optional[float] = None      # 专家评分 (1-5)
    user_rating: Optional[float] = None        # 用户评分 (1-5)
    recommendation_reasons: List[str] = field(default_factory=list)

    # 库存和销售
    stock_status: str = "有货"
    sales_volume: Optional[int] = None
    popularity_score: Optional[float] = None

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, (NutritionalInfo, SafetyInfo)):
                result[key] = value.__dict__ if value else None
            elif isinstance(value, list) and value and isinstance(value[0], Enum):
                result[key] = [item.value for item in value]
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BabyProduct':
        """从字典创建实例"""
        # 处理枚举类型
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = ProductCategory(data['category'])

        if 'age_range' in data and isinstance(data['age_range'], str):
            data['age_range'] = AgeRange(data['age_range'])

        if 'certifications' in data and isinstance(data['certifications'], list):
            data['certifications'] = [CertificationType(cert) if isinstance(cert, str) else cert
                                    for cert in data['certifications']]

        # 处理嵌套对象
        if 'nutritional_info' in data and isinstance(data['nutritional_info'], dict):
            data['nutritional_info'] = NutritionalInfo(**data['nutritional_info'])

        if 'safety_info' in data and isinstance(data['safety_info'], dict):
            data['safety_info'] = SafetyInfo(**data['safety_info'])

        return cls(**data)

    def is_suitable_for_age(self, age_months: int) -> bool:
        """判断是否适合指定月龄"""
        age_ranges = {
            AgeRange.NEWBORN: (0, 3),
            AgeRange.INFANT: (3, 6),
            AgeRange.MOBILE_BABY: (6, 12),
            AgeRange.TODDLER: (12, 24),
            AgeRange.PRESCHOOL: (24, 60),
            AgeRange.ALL_AGES: (0, 60)
        }

        min_age, max_age = age_ranges.get(self.age_range, (0, 60))
        return min_age <= age_months < max_age

    def has_certification(self, cert_type: CertificationType) -> bool:
        """检查是否有指定认证"""
        return cert_type in self.certifications

    def matches_conditions(self, conditions: List[str]) -> bool:
        """检查是否匹配指定条件"""
        if not conditions:
            return True

        product_conditions = [cond.lower() for cond in self.suitable_conditions]
        return any(cond.lower() in product_conditions for cond in conditions)

    def get_price_range_category(self) -> str:
        """获取价格区间分类"""
        if self.price < 100:
            return "经济型"
        elif self.price < 300:
            return "中端"
        elif self.price < 600:
            return "高端"
        else:
            return "奢华"

    def calculate_value_score(self) -> float:
        """计算性价比分数"""
        base_score = 0.0

        # 专家评分权重
        if self.expert_rating:
            base_score += self.expert_rating * 0.4

        # 用户评分权重
        if self.user_rating:
            base_score += self.user_rating * 0.3

        # 认证加分
        cert_bonus = len(self.certifications) * 0.1
        base_score += min(cert_bonus, 0.5)  # 最多加0.5分

        # 高端特性加分
        feature_bonus = len(self.premium_features) * 0.05
        base_score += min(feature_bonus, 0.3)  # 最多加0.3分

        return min(base_score, 5.0)  # 最高5分

    def get_recommendation_summary(self) -> str:
        """获取推荐摘要"""
        summary_parts = []

        # 品牌和产品名
        summary_parts.append(f"{self.brand} {self.name}")

        # 主要特性
        if self.premium_features:
            top_features = self.premium_features[:2]
            summary_parts.append(f"特色: {', '.join(top_features)}")

        # 认证信息
        if self.certifications:
            cert_names = [cert.value for cert in self.certifications[:2]]
            summary_parts.append(f"认证: {', '.join(cert_names)}")

        # 适用年龄
        summary_parts.append(f"适合: {self.age_range.value}")

        return " | ".join(summary_parts)

class ProductDatabase:
    """母婴商品数据库管理类"""

    def __init__(self):
        self.products: Dict[str, BabyProduct] = {}
        self.category_index: Dict[ProductCategory, List[str]] = {}
        self.brand_index: Dict[str, List[str]] = {}
        self.age_index: Dict[AgeRange, List[str]] = {}

    def add_product(self, product: BabyProduct) -> bool:
        """添加商品"""
        try:
            self.products[product.product_id] = product

            # 更新索引
            self._update_indexes(product)

            return True
        except Exception as e:
            print(f"❌ 添加商品失败: {e}")
            return False

    def _update_indexes(self, product: BabyProduct):
        """更新索引"""
        # 分类索引
        if product.category not in self.category_index:
            self.category_index[product.category] = []
        if product.product_id not in self.category_index[product.category]:
            self.category_index[product.category].append(product.product_id)

        # 品牌索引
        if product.brand not in self.brand_index:
            self.brand_index[product.brand] = []
        if product.product_id not in self.brand_index[product.brand]:
            self.brand_index[product.brand].append(product.product_id)

        # 年龄索引
        if product.age_range not in self.age_index:
            self.age_index[product.age_range] = []
        if product.product_id not in self.age_index[product.age_range]:
            self.age_index[product.age_range].append(product.product_id)

    def get_product(self, product_id: str) -> Optional[BabyProduct]:
        """获取商品"""
        return self.products.get(product_id)

    def search_products(self, category: Optional[ProductCategory] = None,
                       brand: Optional[str] = None,
                       age_range: Optional[AgeRange] = None,
                       max_price: Optional[float] = None,
                       conditions: Optional[List[str]] = None) -> List[BabyProduct]:
        """搜索商品"""
        results = list(self.products.values())

        # 按分类筛选
        if category:
            results = [p for p in results if p.category == category]

        # 按品牌筛选
        if brand:
            results = [p for p in results if p.brand.lower() == brand.lower()]

        # 按年龄筛选
        if age_range:
            results = [p for p in results if p.age_range == age_range]

        # 按价格筛选
        if max_price:
            results = [p for p in results if p.price <= max_price]

        # 按条件筛选
        if conditions:
            results = [p for p in results if p.matches_conditions(conditions)]

        return results

    def get_top_products(self, category: Optional[ProductCategory] = None,
                        limit: int = 10) -> List[BabyProduct]:
        """获取热门商品"""
        products = self.search_products(category=category)

        # 按综合评分排序
        products.sort(key=lambda p: (
            p.calculate_value_score(),
            p.popularity_score or 0,
            p.sales_volume or 0
        ), reverse=True)

        return products[:limit]

    def export_to_json(self, filepath: str) -> bool:
        """导出到JSON文件"""
        try:
            data = {
                "products": [product.to_dict() for product in self.products.values()],
                "exported_at": datetime.now().isoformat(),
                "total_count": len(self.products)
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False

    def load_from_json(self, filepath: str) -> bool:
        """从JSON文件加载"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for product_data in data.get("products", []):
                product = BabyProduct.from_dict(product_data)
                self.add_product(product)

            print(f"✅ 成功加载 {len(self.products)} 个商品")
            return True
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False