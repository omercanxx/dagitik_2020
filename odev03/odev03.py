import matplotlib.pyplot as plt
from datetime import datetime

def shift_list(array, s):
    s %= len(array)
    s *= -1
    shifted_array = array[s:] + array[:s]
    return shifted_array

def add_values_in_dict(sample_dict, key, list_of_values):
    if key not in sample_dict:
        sample_dict[key] = list()
    sample_dict[key].append(list_of_values)
    return sample_dict

def add_values_in_dictcircular(c, sample_dict, key, list_of_values):
    if c < 100:
        if key not in sample_dict:
            sample_dict[key] = list()
        sample_dict[key].append(list_of_values)
    else:
        sample_dict[key] = shift_list(sample_dict[key], - 1)
        sample_dict[key][len(sample_dict[key]) - 1] = list_of_values
        add_values_in_dict(freq_dict, key, calculate(100, sample_dict[key][len(sample_dict[key]) - 1], sample_dict[key][0]))
    return sample_dict


def search(list, platform):
    for i in range(len(list)):
        if list[i] == int(platform):
            return i

def calculate(w, last_time, first_time):
    if last_time == first_time:
        print('error')
        return False

    return w / (float(last_time) - float(first_time))

count = 0
data_dict = dict()
time_dict = dict()
freq_dict = dict()
min_dict = dict()
max_dict = dict()
blank = dict()
zero = dict()

with open("data/lab8_2.09-0.32-1.52.mbd") as file:
    for lines in file:
        line = lines.split(",")
        line[-1] = line[-1].strip()
        sensor_mac = line[1]
        transmitter_mac = line[2]
        mac = (sensor_mac, transmitter_mac)
        data_dict = add_values_in_dict(data_dict, mac, line[-1])

        #minimumu bulma
        temp = min(data_dict[mac])
        res = [key for key in data_dict if data_dict[key] == temp]
        min_dict[mac] = temp

        #maximumu bulma
        temp = max(data_dict[mac])
        res = [key for key in data_dict if data_dict[key] == temp]
        max_dict[mac] = temp

for key in data_dict:
    blank[key] = list(range(int(max_dict[key]), int(min_dict[key]) + 1))
    zero[key] = [0 for i in range(int(max_dict[key]), int(min_dict[key]) + 1)]
    for value in data_dict[key]:
        n = search(blank[key], value)
        zero[key][n] += 1
    plt.bar(blank[key], zero[key], color='maroon', width=0.4)
    plt.title(key)
    plt.show()
file.close()

with open("data/lab8_2.09-0.32-1.52.mbd") as file:
    for lines in file:
        count += 1
        line = lines.split(",")
        line[-1] = line[-1].strip()
        sensor_mac = line[1]
        transmitter_mac = line[2]
        mac = (sensor_mac, transmitter_mac)
        time_dict = add_values_in_dictcircular(count, time_dict, mac, line[0])

for key in data_dict:
    for value in freq_dict[key]:
        value = float(value)
    x = range(len(freq_dict[key]))
    plt.plot(x, freq_dict[key], color='maroon')
    plt.title(key)
    plt.show()