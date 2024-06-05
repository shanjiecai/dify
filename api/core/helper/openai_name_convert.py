# openai messages name参数格式转换
def correct_name_field(input_string):
    import re
    # Replace spaces and symbols with '-', allowing only alphanumeric characters, '-', and '_'
    # corrected_string = re.sub(r'[^a-zA-Z0-9_-]+', '-', input_string)
    corrected_string = re.sub(r'[^a-zA-Z0-9_-]+$', '', input_string)
    corrected_string = re.sub(r'[^a-zA-Z0-9_-]+', '-', corrected_string)
    return corrected_string


if __name__ == "__main__":
    # Test the function with various inputs
    # test_inputs = ["John Doe", "User 123!", "name@domain.com", "Jimmy·God"]
    test_inputs = ["Mauro Gutiérrez(4)"]
    corrected_names = [correct_name_field(name) for name in test_inputs]

    print(corrected_names)

