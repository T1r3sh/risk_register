# main_plot
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from db_operation_functions import queryComposer
import mplcursors
import matplotlib.dates as mdates


def wrap_string(string, max_length):
    lines = []
    current_line = ""
    for word in string.split():
        if len(current_line) + len(word) > max_length:
            lines.append(current_line.strip())
            current_line = ""
        current_line += word + " "
    lines.append(current_line.strip())
    return "\n".join(lines)


def risk_matrix_():
    # font settings
    plt.rcParams["font.family"] = "Calibri"

    # data setup
    qcrr = queryComposer("risk_register")
    raw_risk_data = qcrr.select_query(order_opt=["risk_id"])
    risk_data_id_ref = {risk["risk_id"]: risk for risk in raw_risk_data}
    qcrr.close_connection()
    qcrc = queryComposer("risk_classification")
    raw_class_data = qcrc.select_query(order_opt=["risk_class_id"])
    qcrc.close_connection()
    risk_class_data_id_ref = {
        r_class["risk_class_id"]: r_class for r_class in raw_class_data
    }
    risk_data_xy_ref = {
        (risk["risk_prob"] / 5, risk["risk_damage"] / 10): {
            "risk_id": risk["risk_id"],
            "risk_name": risk["risk_name"],
            "risk_class_name": risk_class_data_id_ref[risk["risk_class_id"]][
                "risk_class_name"
            ],
        }
        for risk in raw_risk_data
        if risk["risk_prob"] is not None
    }
    # Define the positions for the colors in the colormap
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]
    positions = [0, 0.5, 1]
    cmap = LinearSegmentedColormap.from_list(
        "my_colormap", list(zip(positions, colors))
    )

    # background filling
    n = 100
    x, y = np.meshgrid(np.linspace(0, 20, 40), np.linspace(0, 10, 20))
    chmap = (x + y) / 3
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.canvas.toolbar.visible = False
    heatmap = ax.imshow(
        chmap, cmap=cmap, alpha=0.7, origin="lower", extent=[0, 20, 0, 10]
    )

    # annotation and label setup
    ax.set_title("Матрица рисков", fontsize=16)
    ax.set_xticks([2, 6, 10, 14, 18])
    ax.set_xticklabels(
        ["Очень низкий", "Низкий", "Средний", "Высокий", "Очень высокий"], fontsize=12
    )
    ax.set_ylabel("Вероятность возникновения", fontsize=14)
    ax.set_yticks([1, 3, 5, 7, 9])
    ax.set_yticklabels(
        ["Очень низкая", "Низкая", "Средняя", "Высокая", "Очень высокая"], fontsize=12
    )
    ax.set_xlabel("Масштаб повреждений(ущерб)", fontsize=14)
    # grid to make possible place labels between lines
    ax.axhline(y=2, color="grey", alpha=0.5)
    ax.axhline(y=4, color="grey", alpha=0.5)
    ax.axhline(y=6, color="grey", alpha=0.5)
    ax.axhline(y=8, color="grey", alpha=0.5)
    ax.axvline(x=4, color="grey", alpha=0.5)
    ax.axvline(x=8, color="grey", alpha=0.5)
    ax.axvline(x=12, color="grey", alpha=0.5)
    ax.axvline(x=16, color="grey", alpha=0.5)
    # get rid of whitespaces
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="both", which="both", length=0)
    # colorbar setup
    cbar = fig.colorbar(heatmap)
    cbar.set_label("Уровень риска", fontsize=14)
    # risk setup
    fig.canvas.manager.set_window_title("Матрица рисков")
    scatters = []
    for risk_id, risk_info in risk_data_id_ref.items():
        x = 0 if risk_info["risk_prob"] is None else risk_info["risk_prob"] / 5
        y = 0 if risk_info["risk_damage"] is None else risk_info["risk_damage"] / 10
        scatter = ax.scatter(
            x, y, s=500, alpha=0.8, facecolor="white", edgecolors="black"
        )
        ax.text(x, y, risk_id, ha="center", va="center", fontsize=14, fontweight="bold")
        scatters.append(scatter)

    cursor = mplcursors.cursor(scatters, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        xy = tuple(sel.target)
        if xy not in risk_data_xy_ref.keys():
            sel.annotation.set_text("Unknown risk")
            return
        tmp_data = risk_data_xy_ref[xy]
        risk_id = tmp_data["risk_id"]
        wrapped_name_s = wrap_string(tmp_data["risk_name"], 70)
        risk_name = f"Риск {risk_id}: {wrapped_name_s}\n{tmp_data['risk_class_name']}"
        sel.annotation.set(
            wrap=True, alpha=1, color="white", backgroundcolor="blue", clip_on=True
        )
        sel.annotation.set_text(risk_name)

    # Show the plot
    plt.show()


def last_sensor_plot(sensor_id: int, period: str = "hour"):
    if period not in ["hour", "week", "day", "minute"]:
        raise ValueError("Invalid period param")

    qcs = queryComposer("sensor")
    cond = [
        {
            "key_name": "sensor_id",
            "comp_operand": "=",
            "key_value": sensor_id,
        }
    ]
    sensor_data = qcs.select_query(conditions=cond)[0]
    qcs.close_connection()
    limit_val = sensor_data["limit_mode_value"]
    sensor_name = sensor_data["sensor_name"]

    qcu = queryComposer("sensor_unit")
    cond = [
        {
            "key_name": "unit_id",
            "comp_operand": "=",
            "key_value": sensor_data["unit_id"],
        }
    ]
    unit_data = qcu.select_query(conditions=cond)[0]
    qcu.close_connection()
    unit_name = unit_data["unit_name"]

    qc = queryComposer("sensor_logs")
    cond = [
        {
            "key_name": "sensor_id",
            "comp_operand": "=",
            "key_value": sensor_id,
        },
        {
            "key_name": "log_datetime",
            "comp_operand": ">=",
            "key_value": f"now()-interval '1 {period}'",
        },
        {
            "key_name": "log_datetime",
            "comp_operand": "<=",
            "key_value": "now()",
        },
    ]
    raw_data = qc.select_query(conditions=cond, order_opt=["log_datetime"])
    qc.close_connection()

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.canvas.manager.set_window_title("Дополнительные графики")
    if not raw_data:
        fig.show()
        return
    first_rec = raw_data.pop(0)
    x_data = [first_rec["log_datetime"]]
    y_data = [first_rec["sensor_value"]]
    if period == "hour":
        for rec in raw_data:
            if (rec["log_datetime"] - x_data[-1]).total_seconds() >= 5:
                x_data.append(rec["log_datetime"])
                y_data.append(rec["sensor_value"])
        minutes_10 = mdates.MinuteLocator(interval=5)
        ax.xaxis.set_major_locator(minutes_10)
        time_fmt = mdates.DateFormatter("%H:%M")
        ax.xaxis.set_major_formatter(time_fmt)
        fig.canvas.manager.set_window_title("График за прошлый час")
        ax.set_xlabel("Время")
    elif period == "week":
        for rec in raw_data:
            if (rec["log_datetime"] - x_data[-1]).total_seconds() >= 15 * 60:
                x_data.append(rec["log_datetime"])
                y_data.append(rec["sensor_value"])
        ax.set_xlabel("Дата")
        ax.set_xticks(list({date.date() for date in x_data}))
        ax.set_xticklabels(list({date.date() for date in x_data}))
        fig.canvas.manager.set_window_title("График за прошлую неделю")
    elif period == "day":
        for rec in raw_data:
            if (rec["log_datetime"] - x_data[-1]).total_seconds() >= 5 * 60:
                x_data.append(rec["log_datetime"])
                y_data.append(rec["sensor_value"])
        ax.set_xlabel("Время")
        dates = mdates.HourLocator(interval=2)
        date_fmt = mdates.DateFormatter("%H:%M")
        ax.xaxis.set_major_formatter(date_fmt)
        ax.xaxis.set_major_locator(dates)
        fig.canvas.manager.set_window_title("График за прошлый день")

    ax.set_title(f"{sensor_name}")
    ax.set_ylabel(f"Значения, {unit_name}")
    ax.grid()
    ax.axhline(
        y=0.8 * limit_val,
        linestyle="--",
        color="red",
        dashes=(5, 5),
    )
    fig.canvas.toolbar.visible = False
    ax.set_ylim(0, limit_val)
    ax.plot(x_data, y_data)
    plt.show()


if __name__ == "__main__":
    risk_matrix_()  # (1, "hour")
