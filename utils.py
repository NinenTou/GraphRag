from datetime import datetime, timedelta
from email.mime.text import MIMEText
import random
import string
from app.MySQL.database import get_user_db_connection

def generate_verification_code(length=4):
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))

def save_verification_code(email, code, code_type, expiry_minutes=5):
    """保存验证码到数据库"""
    try:
        cursor = get_user_db_connection().cursor()
        # 先标记旧验证码为已使用
        cursor.execute('''
            UPDATE verification_codes 
            SET is_used = TRUE 
            WHERE email = %s AND type = %s
        ''', (email, code_type))
        
        # 插入新验证码
        cursor.execute('''
            INSERT INTO verification_codes (email, code, type, is_used)
            VALUES (%s, %s, %s, FALSE)
        ''', (email, code, code_type))
        get_user_db_connection().commit()
        cursor.close()
        return True
    
    except Exception as e:
        print(f"保存验证码失败: {str(e)}")
        return False

def validate_verification_code(email, code, code_type):
    """验证验证码是否有效"""
    try:
        connection = get_user_db_connection()
        cursor = get_user_db_connection().cursor()
        cursor.execute('''
            SELECT id, code, created_at 
            FROM verification_codes 
            WHERE email = %s AND type = %s AND is_used = FALSE
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (email, code_type))
        result = cursor.fetchone()
        
        if not result:
            return False
            
        code_id, stored_code, created_at = result
        
        # 检查是否过期（5分钟）
        if datetime.now() > created_at + timedelta(minutes=5):
            return False
            
        # 标记为已使用
        cursor.execute('''
            UPDATE verification_codes 
            SET is_used = TRUE 
            WHERE id = %s
        ''', (code_id,))
        connection.commit()
        cursor.close()
        
        return stored_code == code
    except Exception as e:
        print(f"验证验证码失败: {str(e)}")
        return False

def send_email(to_email, subject, content):
    """发送邮件"""
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr(('文件分析系统', config.EMAIL_CONFIG['MAIL_USERNAME']))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        server = smtplib.SMTP_SSL(config.EMAIL_CONFIG['MAIL_SERVER'], config.EMAIL_CONFIG['MAIL_PORT'])
        server.login(config.EMAIL_CONFIG['MAIL_USERNAME'], config.EMAIL_CONFIG['MAIL_PASSWORD'])
        server.sendmail(config.EMAIL_CONFIG['MAIL_USERNAME'], [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False 