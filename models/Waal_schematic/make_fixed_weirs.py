import os


with open('fixed_weirs.pliz', 'w') as FWRITE:
    # Kribben
    for gi in range(30):
        with open('groyne{:02d}.pli'.format(gi), 'r') as f:
            FWRITE.write('{}:type=groyne\n'.format(f.readline().strip()))
            FWRITE.write('2 9\n')
            f.readline()
            for i in range(2):
                x, y = map(float, f.readline().split(' '))
                FWRITE.write('{} {} 3 0 0 3.0 4.0 4.0 0\n'.format(x, y))
    # Langsdammen
    for gi in range(30):
        """
        with open('LTD{:02d}.pli'.format(gi), 'r') as f:
            FWRITE.write('{}:type=groyne\n'.format(f.readline().strip()))
            FWRITE.write('2 9\n')
            f.readline()
            for i in range(2):
                x, y = map(float, f.readline().split(' '))
                FWRITE.write('{} {} 3 0 0 3.0 4.0 4.0 0\n'.format(x, y))
        """