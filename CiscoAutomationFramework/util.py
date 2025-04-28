from ipaddress import ip_address

def abbreviate_interface(interface_string, max_chars=2):
    return interface_string[:max_chars] + ''.join([char for char in interface_string if not char.isalpha()])

def is_ipv4(addr):
    try:
        _=ip_address(addr)
        return True
    except:
        return False
    
def column_print(data, spaces_between_columns=2, separator_char=None):
    column_widths = []
    for index, _ in enumerate(data[0]):
        column_widths.append(max(len(str(row[index])) for row in data) + spaces_between_columns)

    if separator_char and type(separator_char) is str and len(separator_char) == 1:
        separator_line = [[separator_char * (x - spaces_between_columns) for x in column_widths]]
        first_line = data[:1]
        rest = data[1:]
        data = first_line + separator_line + rest


    for row in data:
        print_string = ''
        for index, word in enumerate(row):
            print_string += str(word).ljust(column_widths[index])
        print(print_string)

def chunker(list, size):
    end_list = []
    for i in range(0, len(list), size):
        end_list.append(list[i:i + size])
    return end_list
