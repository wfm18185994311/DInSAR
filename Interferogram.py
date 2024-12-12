import os
import shutil
import esa_snappy
from esa_snappy import ProductIO, GPF, HashMap, jpy
from datetime import datetime

# 获取 Java 类型
Integer = jpy.get_type('java.lang.Integer')
Double = jpy.get_type('java.lang.Double')  # 定义 Double 类型
String = jpy.get_type('java.lang.String')  # 定义 String 类型

# 读取产品
def read_product(product_path):
    try:
        return ProductIO.readProduct(product_path)
    except Exception as e:
        print(f"读取产品时出错: {e}")
        exit(1)

# 应用分割
def apply_split(product):
    try:
        parameters = HashMap()
        parameters.put("subswath", "IW2")
        parameters.put("selectedPolarisations", "VV")
        parameters.put("firstBurstIndex", Integer(1))  # 使用 Java Integer 类型
        parameters.put("lastBurstIndex", Integer(3))   # 使用 Java Integer 类型
        return GPF.createProduct('TOPSAR-Split', parameters, product)
    except Exception as e:
        print(f"应用分割时出错: {e}")
        exit(1)

# 应用轨道文件
def apply_orbit_file(product):
    try:
        parameters = HashMap()
        parameters.put("orbitType", "Sentinel Precise (Auto Download)")
        parameters.put("polyDegree", Integer(3))  # 使用 Java Integer 类型
        return GPF.createProduct('Apply-Orbit-File', parameters, product)
    except Exception as e:
        print(f"应用轨道文件时出错: {e}")
        exit(1)

# 应用 Enhanced Spectral Diversity (ESD)
def apply_esd(product):
    try:
        parameters = HashMap()

        # 根据截图中的参数进行配置
        parameters.put("Registration_Window_Width", Integer(512))
        parameters.put("Registration_Window_Height", Integer(512))
        parameters.put("Search_Window_Accuracy_in_Azimuth_Direction", Integer(16))
        parameters.put("Search_Window_Accuracy_in_Range_Direction", Integer(16))
        parameters.put("Window_Oversampling_Factor", Integer(128))
        parameters.put("Cross_Correlation_Threshold", Double(0.1))
        parameters.put("Coherence_Threshold_for_Outlier_Removal", Double(0.3))
        parameters.put("Number_of_Windows_Per_Overlap_for_ESD", Integer(10))
        parameters.put("ESD_Estimator", "Periodogram")
        parameters.put("Weight_Function", "Inv Quadratic")
        parameters.put("Temporal_Baseline_Type", "Number of images")
        parameters.put("Maximum_Temporal_Baseline", "Number of images")
        parameters.put("Integration_Method", "L1 and L2")
        parameters.put("Overall_Range_Shift_in_Pixels", Double(0.0))
        parameters.put("Overall_Azimuth_Shift_in_Pixels", Double(0.0))

        # 执行 ESD 操作
        return GPF.createProduct('Enhanced-Spectral-Diversity', parameters, product)
    except Exception as e:
        print(f"应用 ESD 时出错: {e}")
        exit(1)

# 应用配准
def apply_back_geocoding(master_product, slave_product, dem_file_path):
    try:
        if master_product is None or slave_product is None:
            raise ValueError("主产品或从产品为 None，无法进行配准")
        # 检查 DEM 文件是否存在
        if not os.path.exists(dem_file_path):
            raise ValueError(f"DEM 文件不存在: {dem_file_path}")

        parameters = HashMap()
        parameters.put("demResamplingMethod", "BILINEAR_INTERPOLATION")
        parameters.put("externalDEMFile", dem_file_path)

        # 使用 Double(0.0) 代替 Integer(0)，确保传递的是 double 类型
        parameters.put("externalDEMNoDataValue", Double(0.0))  # 使用 Java Double 类型

        parameters.put("maskOutAreaWithoutElevation", False)
        parameters.put("outputRangeAzimuthOffset", False)
        parameters.put("outputDerampDemodPhase", False)

        master_slave = HashMap()
        master_slave.put("Master", master_product)
        master_slave.put("Slave", slave_product)

        return GPF.createProduct("Back-Geocoding", parameters, master_slave)
    except Exception as e:
        print(f"应用配准时出错: {e}")
        exit(1)

# 应用 Deburst
def apply_deburst(product):
    try:
        parameters = HashMap()
        return GPF.createProduct('TOPSAR-Deburst', parameters, product)
    except Exception as e:
        print(f"应用 Deburst 时出错: {e}")
        exit(1)

# 应用干涉图生成
def apply_interferogram_formation(product, dem_file_path):
    try:
        parameters = HashMap()
        parameters.put('subtractFlatEarthPhase', True)
        parameters.put('degree', Integer(5))
        parameters.put('numPoints', Integer(501))
        parameters.put('orbitDegree', Integer(3))
        parameters.put('subtractTopographicPhase', True)
        parameters.put('externalDEMFile', dem_file_path)
        parameters.put('externalDEMNoDataValue', Double(0.0))
        parameters.put('tileExtensionPercent', String('100'))
        parameters.put('includeCoherence', True)

        return GPF.createProduct('Interferogram', parameters, product)
    except Exception as e:
        print(f"应用干涉图生成时出错: {e}")
        exit(1)


# 保存产品
def save_product(product, output_path):
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        ProductIO.writeProduct(product, output_path, 'BEAM-DIMAP')
    except Exception as e:
        print(f"保存产品时出错: {e}")
        exit(1)

# 获取产品时间
def get_product_time(safe_file):
    basename = os.path.basename(safe_file)  # 获取文件夹名
    try:
        timestamp_str = basename.split('_')[5]  # 第六段为日期时间
        return datetime.strptime(timestamp_str, "%Y%m%dT%H%M%S")
    except (IndexError, ValueError) as e:
        print(f"无法解析文件名中的时间戳: {basename}. 错误: {e}")
        raise

# 数据处理流程
def process_data(input_safe_files, output_path, dem_file_path):
    master_product = None
    input_safe_files.sort(key=get_product_time)  # 按时间排序

    for safe_file in input_safe_files:
        # 读取产品
        product = read_product(safe_file)

        # Apply split
        split_product = apply_split(product)

        # Apply orbit file
        orbit_applied_product = apply_orbit_file(split_product)

        if master_product is None:
            # 处理时间最早的产品，保存并设置为主产品
            master_product = orbit_applied_product
            output_file_path = os.path.join(output_path, os.path.basename(safe_file).replace('.SAFE', '_split_orbit.dim'))
            save_product(orbit_applied_product, output_file_path)
        else:
            # 对接下来的产品进行配准
            back_geocoded_product = apply_back_geocoding(master_product, orbit_applied_product, dem_file_path)
            output_file_path = os.path.join(output_path, os.path.basename(safe_file).replace('.SAFE', '_split_orbit_backgeo.dim'))
            save_product(back_geocoded_product, output_file_path)

            # 应用 Enhanced Spectral Diversity (ESD)
            esd_applied_product = apply_esd(back_geocoded_product)
            esd_output_file_path = os.path.join(output_path, os.path.basename(safe_file).replace('.SAFE', '_esd.dim'))
            save_product(esd_applied_product, esd_output_file_path)

            # 应用 TOPSAR-Deburst
            deburst_applied_product = apply_deburst(esd_applied_product)
            deburst_output_file_path = os.path.join(output_path, os.path.basename(safe_file).replace('.SAFE', '_deburst.dim'))
            save_product(deburst_applied_product, deburst_output_file_path)

            # 应用干涉图生成
            interferogram_product = apply_interferogram_formation(deburst_applied_product, dem_file_path)
            interferogram_output_file_path = os.path.join(output_path, os.path.basename(safe_file).replace('.SAFE', '_interferogram.dim'))
            save_product(interferogram_product, interferogram_output_file_path)

# 路径定义
input_safe_files = [
    '/data/wangfengmao_file/aipy/input/S1A_IW_SLC__1SDV_20211229T231926_20211229T231953_041230_04E66A_3DBE.SAFE',
    '/data/wangfengmao_file/aipy/input/S1A_IW_SLC__1SDV_20220110T231926_20220110T231953_041405_04EC57_103E.SAFE'
]
output_path = '/data/wangfengmao_file/aipy/output'
dem_file_path = '/data/wangfengmao_file/aipy/dem/utm_srtm_57_05.tif'

# 确保输出路径存在
os.makedirs(output_path, exist_ok=True)

# 运行数据处理流程
process_data(input_safe_files, output_path, dem_file_path)
