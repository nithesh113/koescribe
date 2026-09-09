import QtQuick
import QtQuick.Controls

Button {
    id: control

    property color normalColor: "#20B8AE"
    property color hoverColor: "#29C9BE"
    property color pressedColor: "#16978F"
    property color disabledColor: "#34404B"

    implicitWidth: 190
    implicitHeight: 52

    hoverEnabled: true

    font.pixelSize: 15
    font.weight: Font.DemiBold

    scale: control.pressed ? 0.98 : 1.0

    Behavior on scale {
        NumberAnimation {
            duration: 100
            easing.type: Easing.OutCubic
        }
    }

    contentItem: Item {
        Row {
            anchors.centerIn: parent
            spacing: 10

            Text {
                text: control.text
                color: control.enabled ? "#071311" : "#89939E"
                font.pixelSize: control.font.pixelSize
                font.weight: control.font.weight
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: "→"
                color: control.enabled ? "#071311" : "#89939E"
                font.pixelSize: 19
                font.weight: Font.Bold
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    background: Rectangle {
        radius: 14

        color: {
            if (!control.enabled)
                return control.disabledColor

            if (control.pressed)
                return control.pressedColor

            if (control.hovered)
                return control.hoverColor

            return control.normalColor
        }

        border.width: control.activeFocus ? 2 : 0
        border.color: "#A7FFF7"

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
    }
}