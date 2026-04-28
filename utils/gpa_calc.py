def get_grade_points(grade):
    points = {
        'A+': 10, 'A': 9, 'B+': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0
    }
    return points.get(grade.upper(), 0)

def calculate_gpa(grades_list):
    """
    grades_list: list of dicts with 'grade' and 'course_detail' (containing 'credits')
    """
    if not grades_list:
        return 0.0
    
    total_points = 0
    total_credits = 0
    
    for item in grades_list:
        grade = item.get('grade', 'F')
        # Ensure credits is an int/float
        credits = float(item['course_detail'].get('credits', 0))
        
        total_points += get_grade_points(grade) * credits
        total_credits += credits
        
    if total_credits == 0:
        return 0.0
        
    return round(total_points / total_credits, 2)
