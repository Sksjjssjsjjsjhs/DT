# shuake.py
import time
import sys
from config import setup_driver, Config, setup_logging
from login import dtdjzx_login
from api_utils import APIUtils
from course_learner import CourseLearner

logger = setup_logging()

class Shuake:
    def __init__(self):
        self.driver = setup_driver()
        self.api_utils = APIUtils(self.driver)
        self.learner = CourseLearner(self.driver)
    
    def start(self):
        """主启动方法"""
        try:
            # 登录 - 提供多次机会
            if not dtdjzx_login(self.driver, Config.USERNAME, Config.PASSWORD, max_retries=Config.LOGIN_RETRY_COUNT):
                logger.error("登录失败，程序退出")
                return False
            
            # 检查学习进度（改为检查已完成学时是否达到90）
            total_hours, completed_hours, progress = self.api_utils.get_study_hours()
            try:
                completed = float(completed_hours)
                if completed >= 90:
                    logger.info(f"🎉 已完成{completed}学时，达到目标90学时")
                    self._completion_message()
                    return True
            except ValueError:
                logger.warning("无法解析已完成学时，继续学习")
            
            logger.info(f"当前进度: 已完成{completed_hours}学时 (目标90学时)")
            
            # 获取专栏并学习
            subjects = self.api_utils.get_subjects()
            for subject in subjects:
                result = self.learn_subject(subject)
                
                # 检查是否已完成学习
                if result == "COMPLETED":
                    logger.info(f"🎉 已完成目标90学时")
                    self._completion_message()
                    return True
                elif result:
                    logger.info(f"✅ 专栏完成: {subject['name']}")
                else:
                    logger.warning(f"❌ 专栏学习失败: {subject['name']}")
                
                # 检查总体进度
                _, new_completed, _ = self.api_utils.get_study_hours()
                try:
                    new_completed_num = float(new_completed)
                    if new_completed_num >= 90:
                        logger.info(f"🎉 已完成{new_completed_num}学时，达到目标90学时")
                        self._completion_message()
                        return True
                except ValueError:
                    logger.warning("无法解析已完成学时，继续学习")
            
            # 最终检查进度
            _, final_completed, _ = self.api_utils.get_study_hours()
            try:
                final_completed_num = float(final_completed)
                if final_completed_num >= 90:
                    logger.info(f"🎉 已完成{final_completed_num}学时，达到目标90学时")
                    self._completion_message()
                    return True
                else:
                    logger.info(f"学习结束，最终完成{final_completed_num}学时")
                    return True
            except ValueError:
                logger.info("学习结束，无法获取最终学时")
                return True
            
        except Exception as e:
            logger.error(f"程序执行出错: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def learn_subject(self, subject):
        """学习单个专栏"""
        try:
            logger.info(f"处理专栏: {subject['name']}")
            
            courses = self.api_utils.get_courses(subject['id'])
            courses_to_study = [c for c in courses if c['need_study'] and not c['has_test']]
            
            if not courses_to_study:
                logger.info("没有需要学习的课程")
                return True
            
            logger.info(f"找到 {len(courses_to_study)} 门需要学习的课程")
            
            success_count = 0
            for course in courses_to_study:
                # 传递subject_id给learner
                result = self.learner.learn_course(course, subject['id'])
                
                if result == "COMPLETED":
                    return "COMPLETED"
                elif result:
                    success_count += 1
                    logger.info(f"进度: {success_count}/{len(courses_to_study)}")
                    
                    # 如果不是最后一门课程，等待指定间隔再开始下一门
                    if success_count < len(courses_to_study):
                        logger.info(f"等待{Config.COURSE_INTERVAL}秒后开始下一门课程...")
                        time.sleep(Config.COURSE_INTERVAL)
            
            logger.info(f"本专栏完成: {success_count}/{len(courses_to_study)}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"学习专栏时出错: {str(e)}")
            return False
    
    def _completion_message(self):
        """输出完成消息并终止程序"""
        logger.info("🎉🎉🎉 恭喜！已完成90学时目标 🎉🎉🎉")
        logger.info("程序将在3秒后自动退出...")
        time.sleep(3)
        sys.exit(0)
    
    def cleanup(self):
        """清理资源"""
        try:
            self.driver.quit()
            logger.info("浏览器已关闭")
        except:
            pass

if __name__ == '__main__':
    shuake = Shuake()
    success = shuake.start()
    if success:
        logger.info("程序执行完成")
    else:
        logger.error("程序执行失败")