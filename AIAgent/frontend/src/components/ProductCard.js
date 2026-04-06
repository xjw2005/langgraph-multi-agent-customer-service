import React from 'react';
import { Card, Tag, Space, Typography, Rate, Button, Image } from 'antd';
import { ShoppingCartOutlined, HeartOutlined, StarOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;
const { Meta } = Card;

const ProductCard = ({ product, size = 'default', onAddToCart, onViewDetails }) => {
  const isSmall = size === 'small';

  const renderPrice = () => (
    <Space align="baseline">
      <Text strong style={{ color: '#ff4d4f', fontSize: isSmall ? '14px' : '18px' }}>
        ¥{product.price}
      </Text>
      {product.original_price && product.original_price > product.price && (
        <Text delete type="secondary" style={{ fontSize: isSmall ? '12px' : '14px' }}>
          ¥{product.original_price}
        </Text>
      )}
    </Space>
  );

  const renderFeatures = () => {
    const features = product.premium_features || [];
    const displayFeatures = isSmall ? features.slice(0, 2) : features.slice(0, 3);

    return (
      <Space wrap size="small">
        {displayFeatures.map((feature, index) => (
          <Tag key={index} color="blue" size={isSmall ? 'small' : 'default'}>
            {feature}
          </Tag>
        ))}
      </Space>
    );
  };

  const renderCertifications = () => {
    const certs = product.certifications || [];
    if (certs.length === 0) return null;

    return (
      <Space wrap size="small" style={{ marginTop: '4px' }}>
        {certs.slice(0, 2).map((cert, index) => (
          <Tag key={index} color="green" size="small">
            {cert}
          </Tag>
        ))}
      </Space>
    );
  };

  const renderRating = () => {
    if (!product.expert_rating && !product.user_rating) return null;

    return (
      <Space size="small">
        <Rate
          disabled
          defaultValue={product.expert_rating || product.user_rating || 0}
          style={{ fontSize: isSmall ? '12px' : '14px' }}
        />
        <Text type="secondary" style={{ fontSize: isSmall ? '11px' : '12px' }}>
          {product.expert_rating || product.user_rating}/5
        </Text>
      </Space>
    );
  };

  const cardActions = isSmall ? [] : [
    <Button
      key="cart"
      type="text"
      icon={<ShoppingCartOutlined />}
      onClick={() => onAddToCart?.(product)}
    >
      加入购物车
    </Button>,
    <Button
      key="heart"
      type="text"
      icon={<HeartOutlined />}
    >
      收藏
    </Button>,
    <Button
      key="details"
      type="primary"
      size="small"
      onClick={() => onViewDetails?.(product)}
      style={{ backgroundColor: '#ff69b4', borderColor: '#ff69b4' }}
    >
      查看详情
    </Button>
  ];

  return (
    <Card
      size={isSmall ? 'small' : 'default'}
      hoverable
      actions={cardActions}
      cover={
        <div style={{
          height: isSmall ? '120px' : '200px',
          background: '#f5f5f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}>
          {/* 占位图片 - 实际应用中应该使用真实商品图片 */}
          <div style={{
            width: '80%',
            height: '80%',
            background: 'linear-gradient(45deg, #ff69b4, #ffc0cb)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: isSmall ? '12px' : '16px',
            fontWeight: 'bold'
          }}>
            {product.category}
          </div>

          {/* 原产地标签 */}
          {product.origin_country && (
            <Tag
              color="orange"
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                fontSize: '10px'
              }}
            >
              {product.origin_country}
            </Tag>
          )}
        </div>
      }
      style={{ height: '100%' }}
      bodyStyle={{ padding: isSmall ? '12px' : '16px' }}
    >
      <Meta
        title={
          <div>
            <Title
              level={isSmall ? 5 : 4}
              ellipsis={{ rows: 2 }}
              style={{ margin: 0, fontSize: isSmall ? '13px' : '16px' }}
            >
              {product.name}
            </Title>
            <Text type="secondary" style={{ fontSize: isSmall ? '11px' : '12px' }}>
              {product.brand}
            </Text>
          </div>
        }
        description={
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {/* 价格 */}
            {renderPrice()}

            {/* 评分 */}
            {renderRating()}

            {/* 特色功能 */}
            {renderFeatures()}

            {/* 认证信息 */}
            {renderCertifications()}

            {/* 适用年龄 */}
            {product.age_range && (
              <div>
                <Text style={{ fontSize: isSmall ? '11px' : '12px' }} type="secondary">
                  适合年龄: {product.age_range}
                </Text>
              </div>
            )}

            {/* 简短描述 */}
            {!isSmall && product.description && (
              <Text
                type="secondary"
                ellipsis={{ rows: 2 }}
                style={{ fontSize: '12px', marginTop: '4px' }}
              >
                {product.description}
              </Text>
            )}
          </Space>
        }
      />
    </Card>
  );
};

export default ProductCard;