import multiprocessing
import threading

shared_list = ["parent"]


def change_list():
    shared_list.append("thread")


def child_change_list():
    shared_list.append("process")
    print("В дочернем процессе:", shared_list)


def main():
    global shared_list

    shared_list = ["parent"]
    thread = threading.Thread(target=change_list)
    thread.start()
    thread.join()

    print("После изменения потоком:", shared_list)

    shared_list = ["parent"]

    context = multiprocessing.get_context("fork")
    process = context.Process(target=child_change_list)
    process.start()
    process.join()

    print("В родительском процессе:", shared_list)


if __name__ == "__main__":
    main()
