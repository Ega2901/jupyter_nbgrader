c = get_config()
c.CourseDirectory.course_id = "mycourse"
c.Exchange.root = "/srv/nbgrader/exchange"
c.NbGrader.db_url = "sqlite:///gradebook.db"
c.ExecutePreprocessor.timeout = 120
