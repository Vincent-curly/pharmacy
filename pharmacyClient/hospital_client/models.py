from django.db import models


# Create your models here.
class Role(models.Model):
    """角色信息表"""
    role_name = models.CharField(max_length=50, unique=True, null=False, verbose_name='角色名称')
    permissions = models.ManyToManyField("Permission")
    # 定义角色和权限的多对多关系

    class Meta:
        db_table = 'tb_role'
        verbose_name = verbose_name_plural = '角色信息表'


class Menu(models.Model):
    """菜单"""
    title = models.CharField(max_length=32, unique=True, verbose_name='菜单名称')
    icon = models.CharField(max_length=100, verbose_name='菜单图标', null=True, blank=True)
    menu_type = models.CharField(max_length=10, verbose_name='菜单类型')
    parent = models.ForeignKey("Menu", null=True, blank=True, on_delete=models.CASCADE)
    # 定义菜单间的自引用关系
    # 权限url 在 菜单下；菜单可以有父级菜单；还要支持用户创建菜单，因此需要定义parent字段（parent_id）
    # blank=True 意味着在后台管理中填写可以为空，根菜单没有父级菜单

    def __str__(self):
        # 显示层级菜单
        title_list = [self.title]
        p = self.parent
        while p:
            title_list.insert(0, p.title)
            p = p.parent
        return '-'.join(title_list)

    class Meta:
        db_table = 'tb_menu'
        verbose_name = verbose_name_plural = "菜单"


class Permission(models.Model):
    """权限"""
    title = models.CharField(max_length=32, unique=True, verbose_name='权限')
    url = models.CharField(max_length=128)
    per_id = models.CharField(max_length=100, verbose_name='选项卡id', null=True, blank=True)
    menu = models.ForeignKey("Menu", null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        # 显示带菜单前缀的权限
        return '{menu}---{permission}'.format(menu=self.menu, permission=self.title)

    class Meta:
        db_table = 'tb_authority'
        verbose_name = verbose_name_plural = "权限"


class Company(models.Model):
    """机构信息表"""
    name = models.CharField(max_length=32, unique=True, verbose_name='企业名称')
    tel = models.CharField(max_length=255, verbose_name='企业电话')
    dj_tel = models.CharField(max_length=255, verbose_name='代煎电话(一个或者多个号码，提供给病人，默认康美电话)')
    province = models.CharField(max_length=10, null=False, verbose_name='企业所在省份')
    city = models.CharField(max_length=10, null=False, verbose_name='企业所在城市')
    zone = models.CharField(max_length=10, null=False, verbose_name='企业所在区县')
    address = models.CharField(max_length=200, null=False, verbose_name='企业详细地址')
    introduction = models.CharField(max_length=255, verbose_name='企业介绍')
    company_code = models.CharField(max_length=20, verbose_name='机构编码(由平台分配，调用平台需要用到)')
    company_password = models.CharField(max_length=50, verbose_name='企业密码(调用平台的密码)')
    isnot_showprice = models.IntegerField(verbose_name='价格显示(1：仅显示结算价；2：仅显示销售价；3：结算价销售价全显示；4：结算价销售价全不显示)')
    unitprice = models.FloatField(default=1.5, verbose_name='代煎单价')
    per_pack_dose = models.IntegerField(default=200, verbose_name='每包多少ml')
    sendgoodtime_today = models.CharField(max_length=25, default='18:00:00', verbose_name='送货时间_今天')
    sendgoodtime_tomorrow = models.CharField(max_length=25, default='12:00:00', verbose_name='送货时间_明天')
    createman = models.CharField(max_length=20)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_disabled = models.IntegerField(default=1, verbose_name='账号状态')

    class Meta:
        db_table = 'tb_company'
        verbose_name = verbose_name_plural = '企业信息表'


class ClientUser(models.Model):
    """医院客户端用户信息表"""
    username = models.CharField(max_length=50, unique=True, null=False, verbose_name='用户名')
    password = models.CharField(max_length=100, null=False, verbose_name='密码')
    remark = models.CharField(max_length=100, verbose_name='备注')
    company_id = models.ForeignKey('Company', on_delete=models.CASCADE, verbose_name='企业ID')
    isnot_showprice = models.IntegerField(verbose_name='价格显示(1：仅显示结算价；2：仅显示销售价；3：结算价销售价全显示；4：结算价销售价全不显示)')
    register_time = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    login_time = models.DateTimeField(auto_now_add=False, null=True, verbose_name='最近登录时间')
    is_disabled = models.IntegerField(default=1, verbose_name='是否禁用')
    role = models.ManyToManyField("Role")

    class Meta:
        db_table = 'tb_users'
        verbose_name = verbose_name_plural = '用户信息表'


class Herbs(models.Model):
    """药品信息表"""
    drugs_code = models.CharField(max_length=10, unique=False, verbose_name='商品编码')
    drugs_name = models.CharField(max_length=50, null=False, verbose_name='商品名称')
    short_code = models.CharField(max_length=50, null=False, verbose_name='简码(商品名称首字母大写)')
    price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='价格')
    stock = models.IntegerField(default=0, verbose_name='库存')
    unit = models.CharField(max_length=5, default='g', verbose_name='单位')
    status = models.IntegerField(default=1, verbose_name='是否停用')
    alias1 = models.CharField(max_length=20, verbose_name='别名1')
    alias2 = models.CharField(max_length=20, verbose_name='别名2')
    alias3 = models.CharField(max_length=20, verbose_name='别名3')
    alias4 = models.CharField(max_length=20, verbose_name='别名4')
    alias5 = models.CharField(max_length=20, verbose_name='别名5')
    alias6 = models.CharField(max_length=20, verbose_name='别名6')
    alias7 = models.CharField(max_length=20, verbose_name='别名7')
    alias8 = models.CharField(max_length=20, verbose_name='别名8')
    alias9 = models.CharField(max_length=20, verbose_name='别名9')
    alias10 = models.CharField(max_length=20, verbose_name='别名10')
    goods_norms = models.CharField(max_length=100, null=True, verbose_name='商品规格')
    goods_orgin = models.CharField(max_length=100, null=True, verbose_name='商品产地')
    drugs_type = models.SmallIntegerField(default='0', verbose_name='商品(药材)类型:0 中药，1 西药')
    update_man = models.CharField(max_length=20, null=True, verbose_name='主要记录修改者，方便追溯')
    create_time = models.DateTimeField(null=True, auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(null=True, auto_now=True, verbose_name='数据更新时间')
    company_id = models.CharField(max_length=20, null=True, verbose_name='企业ID')
    sale_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='销售价格')
    isnot_handedit = models.IntegerField(default='0', verbose_name='价格是否被手工干预的标志 0 未干预 1 手工干预')

    class Meta:
        db_table = 'tb_herbs'
        verbose_name = verbose_name_plural = '药品信息表'


class Prescription(models.Model):
    """处方表类"""
    prescri_id = models.CharField(max_length=36, null=False, primary_key=True, verbose_name='处方ID')
    treat_card_id = models.CharField(max_length=36, null=True, verbose_name='诊疗卡号')
    user_name = models.CharField(max_length=20, null=False, verbose_name='患者姓名')
    age = models.IntegerField(null=False, verbose_name='患者年龄')
    gender = models.IntegerField(null=False, verbose_name='患者性别 0 女，1 男，2 未知(病人没有登记性别的情况下)')
    tel = models.CharField(max_length=50, null=False, verbose_name='患者电话')
    is_pregnant = models.IntegerField(verbose_name='是否为孕妇 0 非孕妇，1 孕妇, 2 未知')
    is_hos = models.IntegerField(null=False, verbose_name='处方来源类型 0 默认,1门诊,2住院,3 其他')
    is_suffering = models.IntegerField(null=False, verbose_name='是否煎煮 取值范围：0 否，1 是')
    amount = models.IntegerField(null=False, verbose_name='剂数(付数)')
    suffering_num = models.IntegerField(null=False, verbose_name='煎煮袋数')
    ji_fried = models.IntegerField(verbose_name='几煎')
    prescri_type = models.IntegerField(verbose_name='处方类型 0:中药，1:西药，2:膏方，3:免煎颗粒')
    is_within = models.IntegerField(null=False, verbose_name='服用方式 0 内服，1 外用')
    special_instru = models.CharField(max_length=100, null=True, verbose_name='处方特殊说明 诊断信息')
    bed_num = models.CharField(max_length=50, null=True, verbose_name='床位号')
    hos_depart = models.CharField(max_length=50, null=True, verbose_name='医院科室')
    hospital_num = models.CharField(max_length=50, null=True, verbose_name='住院号')
    disease_code = models.CharField(max_length=50, null=True, verbose_name='病区号')
    doctor = models.CharField(max_length=50, null=True, verbose_name='医生姓名')
    paste_desc_file = models.CharField(max_length=100, null=True, verbose_name='膏方描述')
    prescript_remark = models.CharField(max_length=120, null=True, verbose_name='处方备注')
    per_pack_num = models.IntegerField(verbose_name='每剂几包')
    per_pack_dose = models.IntegerField(verbose_name='每包多少ml')
    medication_methods = models.CharField(max_length=50, null=True, verbose_name='用药方法')
    medication_instruction = models.CharField(max_length=50, null=True, verbose_name='用药指导')
    sea_doctor_time = models.CharField(max_length=50, null=True, verbose_name='就诊时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='处方创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='数据更新时间')
    company_id = models.CharField(max_length=20, null=True, verbose_name='企业ID')
    suffering_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='煎煮费用')
    drug_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='药品结算总价')
    drug_sale_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='药品销售总价')
    pres_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='处方结算总价')
    pres_sale_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='处方销售总价')
    is_order = models.IntegerField(default=0, verbose_name='是否生成订单 0 未生成,n 第n次生成订单')
    order_status = models.SmallIntegerField(default=0, verbose_name='状态 未推送0-推送成功-1-取消推送99-推送失败>1')

    def obj2dict(obj):
        return {'prescri_id': obj.prescri_id, 'user_name': obj.user_name, 'age': obj.age,
                'tel': obj.tel, 'gender': obj.gender, 'is_pregnant': obj.is_pregnant,
                'is_hos': obj.is_hos, 'is_suffering': obj.is_suffering, 'amount': obj.amount,
                'suffering_num': obj.suffering_num, 'ji_fried': obj.ji_fried,
                'prescri_type': obj.prescri_type, 'is_within': obj.is_within,
                'special_instru': obj.special_instru, 'bed_num': obj.bed_num,
                'hos_depart': obj.hos_depart, 'hospital_num': obj.hospital_num,
                'disease_code': obj.disease_code, 'doctor': obj.doctor,
                'paste_desc_file': obj.paste_desc_file, 'prescript_remark': obj.prescript_remark,
                'per_pack_num': obj.per_pack_num, 'per_pack_dose': obj.per_pack_dose,
                'medication_methods': obj.medication_methods,
                'medication_instruction': obj.medication_instruction,
                'sea_doctor_time': obj.sea_doctor_time}

    class Meta:
        db_table = 'tb_prescriptions'
        verbose_name = verbose_name_plural = '处方信息'


class PresDetails(models.Model):
    """处方明细(药材)表类"""
    prescri_id = models.ForeignKey('Prescription', on_delete=models.CASCADE, null=False, verbose_name='处方ID')
    medicines = models.CharField(max_length=100, null=False, verbose_name='药品名')
    drugs_num = models.CharField(max_length=100, null=False, verbose_name='药材编号')
    dose = models.CharField(max_length=10, default='0.00', verbose_name='剂量')
    sum_dose = models.CharField(max_length=10, default='0.00', verbose_name='处方总剂量')
    unit = models.CharField(max_length=50, null=False, verbose_name='单位')
    m_usage = models.CharField(max_length=100, null=True, verbose_name='药品特殊煎法')
    remark = models.CharField(max_length=100, null=True, verbose_name='备注')
    unit_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='结算单价')
    unit_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='结算总价')
    sale_price = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='销售单价')
    sale_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='销售总价')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='数据更新时间')
    update_man = models.CharField(max_length=20, null=True, verbose_name='数据更新人')

    class Meta:
        db_table = 'tb_prescriptions_details'
        verbose_name = verbose_name_plural = '处方明细'


class Order(models.Model):
    """订单表类"""
    order_id = models.CharField(max_length=36, null=False, primary_key=True, verbose_name='订单id')
    treat_card = models.CharField(max_length=50, null=True, verbose_name='诊疗卡号')
    reg_num = models.CharField(max_length=50, null=False, verbose_name='挂单号')
    pres_num = models.ForeignKey('Prescription', on_delete=models.CASCADE, null=True, verbose_name='处方号')
    addr_str = models.CharField(max_length=120, null=False, verbose_name='收货地址')
    provinces = models.CharField(max_length=10, verbose_name='省份')
    city = models.CharField(max_length=10, verbose_name='城市')
    zone = models.CharField(max_length=10, verbose_name='区')
    consignee = models.CharField(max_length=20, null=True, verbose_name='收货人')
    con_tel = models.CharField(max_length=50, null=True, verbose_name='收货人电话')
    send_goods_time = models.CharField(max_length=25, null=True, verbose_name='送货时间')
    is_hos_addr = models.IntegerField(default=0, null=True, verbose_name='是否送医院 0 未知, 1 送医院,2 送病人家里')
    order_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='订单结算总金额')
    order_sale_price_totle = models.DecimalField(max_digits=10, decimal_places=5, default=0, verbose_name='订单销售总金额')
    update_man = models.CharField(max_length=20, null=True, verbose_name='订单更新人')
    update_time = models.DateTimeField(auto_now=True, verbose_name='数据更新时间')
    order_status = models.SmallIntegerField(default=0, verbose_name='状态 未推送0-推送成功-1-取消推送99-推送失败>1')
    push_time = models.DateTimeField(auto_now=True, verbose_name='订单推送时间')
    order_remark = models.CharField(max_length=100, null=True, verbose_name='订单备注')
    company_id = models.CharField(max_length=20, null=True, verbose_name='企业ID')
    creat_man = models.CharField(max_length=20, null=True, verbose_name='订单创建人')
    order_time = models.CharField(max_length=50, null=True, verbose_name='订单时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='订单创建时间')
    zhyf_order_id = models.CharField(max_length=36, null=True, verbose_name='智慧药房订单id')

    class Meta:
        db_table = 'tb_order'
        verbose_name = verbose_name_plural = '订单信息'