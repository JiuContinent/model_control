"""
MySQL数据模型定义
支持多租户和ruoyi_vue_pro数据库的通用数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

# SQLAlchemy基础模型
Base = declarative_base()


class BaseModel(Base):
    """基础模型，包含通用字段"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Boolean, default=False, comment="逻辑删除标记")


class TenantUser(BaseModel):
    """租户用户表"""
    __tablename__ = "tenant_users"
    
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    status = Column(Boolean, default=True, comment="用户状态")
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    
    def __repr__(self):
        return f"<TenantUser(id={self.id}, username={self.username}, tenant_id={self.tenant_id})>"


class TenantRole(BaseModel):
    """租户角色表"""
    __tablename__ = "tenant_roles"
    
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, comment="角色编码")
    description = Column(Text, nullable=True, comment="角色描述")
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    sort_order = Column(Integer, default=0, comment="排序")
    
    def __repr__(self):
        return f"<TenantRole(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"


class TenantMenu(BaseModel):
    """租户菜单表"""
    __tablename__ = "tenant_menus"
    
    name = Column(String(50), nullable=False, comment="菜单名称")
    path = Column(String(200), nullable=True, comment="路由路径")
    component = Column(String(200), nullable=True, comment="组件路径")
    icon = Column(String(100), nullable=True, comment="菜单图标")
    parent_id = Column(Integer, default=0, comment="父菜单ID")
    sort_order = Column(Integer, default=0, comment="排序")
    menu_type = Column(Integer, default=1, comment="菜单类型：1目录，2菜单，3按钮")
    visible = Column(Boolean, default=True, comment="是否显示")
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    
    def __repr__(self):
        return f"<TenantMenu(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"


class SystemLog(BaseModel):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    user_id = Column(Integer, nullable=True, comment="用户ID")
    username = Column(String(50), nullable=True, comment="用户名")
    operation = Column(String(100), nullable=False, comment="操作内容")
    method = Column(String(20), nullable=True, comment="请求方法")
    params = Column(Text, nullable=True, comment="请求参数")
    ip = Column(String(50), nullable=True, comment="IP地址")
    location = Column(String(200), nullable=True, comment="操作地点")
    tenant_id = Column(Integer, nullable=True, comment="租户ID")
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, operation={self.operation}, username={self.username})>"


class AIDetectionRecord(BaseModel):
    """AI检测记录表"""
    __tablename__ = "ai_detection_records"
    
    image_url = Column(String(500), nullable=False, comment="图片URL")
    detection_result = Column(JSON, nullable=True, comment="检测结果JSON")
    confidence = Column(DECIMAL(5, 4), nullable=True, comment="置信度")
    model_name = Column(String(100), nullable=True, comment="模型名称")
    model_version = Column(String(50), nullable=True, comment="模型版本")
    processing_time = Column(DECIMAL(10, 4), nullable=True, comment="处理时间(秒)")
    tenant_id = Column(Integer, nullable=True, comment="租户ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    
    def __repr__(self):
        return f"<AIDetectionRecord(id={self.id}, model_name={self.model_name}, tenant_id={self.tenant_id})>"


class VehicleData(BaseModel):
    """车辆数据表"""
    __tablename__ = "vehicle_data"
    
    vehicle_id = Column(String(50), nullable=False, comment="车辆ID")
    latitude = Column(DECIMAL(10, 8), nullable=True, comment="纬度")
    longitude = Column(DECIMAL(11, 8), nullable=True, comment="经度")
    altitude = Column(DECIMAL(10, 4), nullable=True, comment="海拔")
    speed = Column(DECIMAL(8, 4), nullable=True, comment="速度")
    heading = Column(DECIMAL(6, 2), nullable=True, comment="航向")
    battery_level = Column(DECIMAL(5, 2), nullable=True, comment="电量百分比")
    signal_strength = Column(Integer, nullable=True, comment="信号强度")
    status = Column(String(20), nullable=True, comment="状态")
    raw_data = Column(JSON, nullable=True, comment="原始数据JSON")
    tenant_id = Column(Integer, nullable=True, comment="租户ID")
    
    def __repr__(self):
        return f"<VehicleData(id={self.id}, vehicle_id={self.vehicle_id}, tenant_id={self.tenant_id})>"


class RuoyiUser(BaseModel):
    """若依用户表（兼容ruoyi_vue_pro）"""
    __tablename__ = "ruoyi_users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    dept_id = Column(Integer, nullable=True, comment="部门ID")
    username = Column(String(30), nullable=False, comment="用户账号")
    nickname = Column(String(30), nullable=False, comment="用户昵称")
    user_type = Column(Integer, default=1, comment="用户类型")
    email = Column(String(50), nullable=True, comment="用户邮箱")
    phonenumber = Column(String(11), nullable=True, comment="手机号码")
    sex = Column(Integer, default=0, comment="用户性别")
    avatar = Column(String(512), nullable=True, comment="头像地址")
    password = Column(String(100), nullable=True, comment="密码")
    status = Column(Integer, default=0, comment="帐号状态（0正常 1停用）")
    login_ip = Column(String(128), nullable=True, comment="最后登录IP")
    login_date = Column(DateTime, nullable=True, comment="最后登录时间")
    creator = Column(String(64), nullable=True, comment="创建者")
    updater = Column(String(64), nullable=True, comment="更新者")
    remark = Column(String(500), nullable=True, comment="备注")
    
    # 重写基础字段以匹配若依的命名规范
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Boolean, default=False, comment="是否删除")
    
    def __repr__(self):
        return f"<RuoyiUser(user_id={self.user_id}, username={self.username})>"


class RuoyiRole(BaseModel):
    """若依角色表"""
    __tablename__ = "ruoyi_roles"
    
    role_id = Column(Integer, primary_key=True, autoincrement=True, comment="角色ID")
    role_name = Column(String(30), nullable=False, comment="角色名称")
    role_key = Column(String(100), nullable=False, comment="角色权限字符串")
    role_sort = Column(Integer, nullable=False, comment="显示顺序")
    data_scope = Column(Integer, default=1, comment="数据范围")
    menu_check_strictly = Column(Boolean, default=True, comment="菜单树选择项是否关联显示")
    dept_check_strictly = Column(Boolean, default=True, comment="部门树选择项是否关联显示")
    status = Column(Integer, default=0, comment="角色状态（0正常 1停用）")
    type = Column(Integer, default=2, comment="角色类型")
    creator = Column(String(64), nullable=True, comment="创建者")
    updater = Column(String(64), nullable=True, comment="更新者")
    remark = Column(String(500), nullable=True, comment="备注")
    
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Boolean, default=False, comment="是否删除")
    
    def __repr__(self):
        return f"<RuoyiRole(role_id={self.role_id}, role_name={self.role_name})>"


class RuoyiMenu(BaseModel):
    """若依菜单表"""
    __tablename__ = "ruoyi_menus"
    
    menu_id = Column(Integer, primary_key=True, autoincrement=True, comment="菜单ID")
    menu_name = Column(String(50), nullable=False, comment="菜单名称")
    parent_id = Column(Integer, default=0, comment="父菜单ID")
    order_num = Column(Integer, default=0, comment="显示顺序")
    path = Column(String(200), nullable=True, comment="路由地址")
    component = Column(String(255), nullable=True, comment="组件路径")
    query_param = Column(String(255), nullable=True, comment="路由参数")
    is_frame = Column(Integer, default=1, comment="是否为外链（0是 1否）")
    is_cache = Column(Integer, default=0, comment="是否缓存（0缓存 1不缓存）")
    menu_type = Column(Integer, nullable=False, comment="菜单类型（M目录 C菜单 F按钮）")
    visible = Column(Integer, default=0, comment="显示状态（0显示 1隐藏）")
    status = Column(Integer, default=0, comment="菜单状态（0正常 1停用）")
    perms = Column(String(100), nullable=True, comment="权限标识")
    icon = Column(String(100), nullable=True, comment="菜单图标")
    creator = Column(String(64), nullable=True, comment="创建者")
    updater = Column(String(64), nullable=True, comment="更新者")
    remark = Column(String(500), nullable=True, comment="备注")
    
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Boolean, default=False, comment="是否删除")
    
    def __repr__(self):
        return f"<RuoyiMenu(menu_id={self.menu_id}, menu_name={self.menu_name})>"


# 所有模型的字典，用于批量创建表
ALL_MODELS = {
    "tenant": [TenantUser, TenantRole, TenantMenu, SystemLog, AIDetectionRecord, VehicleData],
    "ruoyi": [RuoyiUser, RuoyiRole, RuoyiMenu]
}
