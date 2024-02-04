from tkinter.filedialog import askdirectory, askopenfilenames
from os import chdir, listdir
import olefile
from struct import unpack


def data_definitions(x):
    return {
        268435715: "WAVELENGTH",
        4097: "CD",
        4134: "g (lum)",
        4135: "Delta I",
        4097: "CD [mdeg]",
        4102: "DC [V]",
        8193: "HT VOLTAGE",
        3: "ABSORBANCE",
        14: "FLUORESCENCE"
    }.get(x, 'undefined')


class JwsHeader:
    def __init__(self, channel_number, point_number,
                 x_for_first_point, x_for_last_point, x_increment, header_names,
                 data_size=None):
        self.channel_number = channel_number
        self.point_number = point_number
        self.x_for_first_point = x_for_first_point
        self.x_for_last_point = x_for_last_point
        self.x_increment = x_increment
        # only defined if this is the header of a v1.5 jws file
        self.data_size = data_size
        self.header_names = header_names


def _unpack_ole_jws_header(data):
    try:
        data_tuple = unpack('<LLLLLLddd', data[0:48])
        # print(data_tuple)
        channels = data_tuple[3]
        nxtfmt = '<L' + 'L' * channels
        header_names = list(unpack(nxtfmt, data[48:48 + 4 * (channels + 1)]))

        for i, e in enumerate(header_names):
            header_names[i] = data_definitions(e)

        data_tuple += tuple(header_names)

        lastPos = 48 + 4 * (channels + 1)
        nxtfmt = '<LLdddd'
        for pos in range(channels):
            data_tuple = data_tuple + unpack(nxtfmt, data[lastPos:lastPos + 40])

        return JwsHeader(data_tuple[3], data_tuple[5],
                         data_tuple[6], data_tuple[7], data_tuple[8], header_names)
    except Exception as e:
        exit("Cannot read DataInfo")


def convert_jws_to_csv(filename):
    with open(filename, "rb") as f:
        f.seek(0)
        oleobj = olefile.OleFileIO(f)

        # print (oleobj.listdir()) lists streams in file
        infos = oleobj.openstream('MeasInfo')
        params = oleobj.openstream('MeasParam')

        data = oleobj.openstream('DataInfo')
        header_data = data.read()
        header_obj = _unpack_ole_jws_header(header_data)
        fmt = 'f' * header_obj.point_number * header_obj.channel_number
        values = unpack(fmt, oleobj.openstream('Y-Data').read())
        chunks = [values[x:x + header_obj.point_number] for x in range(0, len(values), header_obj.point_number)]

    with open(filename.rstrip("jws") + "csv", "w") as r:
        print("file name: %s\t header names: %s" % (filename, header_obj.header_names))
        r.write("sep=,\n")
        r.write(",".join(str(x) for x in header_obj.header_names))
        r.write("\n")
        for line_no in range(header_obj.point_number):
            r.write(str(header_obj.x_for_first_point + line_no * header_obj.x_increment))
            r.write(",")
            for c in range(header_obj.channel_number):
                r.write(str(chunks[c][line_no]))
                r.write(",")
            r.write('\n')
        print("%s is created." % r.name)


if __name__ == "__main__":
    folder = askdirectory(title="Select the folder containing .JWS files to be converted")
    try:
        chdir(folder)
    except OSError:
        exit("Cannot change current working directory.")

    files_found = [x for x in listdir(folder) if x.lower().endswith(".jws")]
    if len(files_found) == 0:
        exit("No .JWS files found.")
    for filename in files_found:
        print(filename)
        convert_jws_to_csv(filename)
