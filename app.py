from flask import Flask, render_template

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("ex1.html")


@app.route("/ex2", methods=["GET"])
def ex2():
    return render_template("ex2.html")


@app.route("/ex3", methods=["GET"])
def ex3():
    return render_template("ex3.html")


@app.route("/ex4", methods=["GET"])
def ex4():
    return render_template("ex4.html")


@app.route("/ex5", methods=["GET"])
def ex5():
    return render_template("ex5.html")


@app.route("/ex6", methods=["GET"])
def ex6():
    return render_template("ex6.html")


@app.route("/ex7", methods=["GET"])
def ex7():
    return render_template("ex7.html")


@app.route("/ex8", methods=["GET"])
def ex8():
    return render_template("ex8.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
