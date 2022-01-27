from builder import *
import sys


def main():
    INDENT = 20

    if len(sys.argv) != 2:
        print(f"Неправильное количество аргументов. Ожидалось 1 но принято: {len(sys.argv)}")
    regexp = sys.argv[1]

    nfda = construct_fnda(regexp)
    print('Полученный по регулярному выражению НКА:')
    nfda.print_table()
    print('-' * INDENT)

    fda = convert_to_fda(nfda)
    print('ДКА полученный по НКА (не минимальный): ')
    fda.print_table()
    print('-' * INDENT)

    min_fda = minimize_fda(fda)
    print('Минимальный ДКА:')
    min_fda.print_table()
    print('-' * INDENT)


if __name__ == '__main__':
    main()
