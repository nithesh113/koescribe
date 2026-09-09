import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: microphonePage

    signal backRequested()
    signal continueRequested()

    Component.onCompleted: microphoneController.refreshMicrophones()

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 46
        anchors.rightMargin: 46
        anchors.topMargin: 28
        anchors.bottomMargin: 26
        spacing: 16

        Text {
            text: "Choose your microphone"
            color: "#F4F1E8"
            font.pixelSize: 32
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true
            text: "Select an input device and speak during the five-second test."
            color: "#98A2B3"
            font.pixelSize: 16
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 100
            radius: 14
            color: "#151B23"
            border.width: 1
            border.color: "#27313D"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                Text {
                    text: "Input device"
                    color: "#D5D9E0"
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }

                ComboBox {
                    id: microphoneSelector
                    Layout.fillWidth: true
                    implicitHeight: 46
                    model: microphoneController.microphones
                    textRole: "name"
                    valueRole: "device_id"
                    enabled: !microphoneController.testing

                    function synchronizeSelection() {
                        for (let index = 0; index < count; index++) {
                            if (valueAt(index) === microphoneController.selectedMicrophoneId) {
                                currentIndex = index
                                return
                            }
                        }
                    }

                    onCountChanged: synchronizeSelection()
                    onActivated: microphoneController.selectMicrophone(currentValue)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 200
            radius: 16
            color: "#111820"
            border.width: 1
            border.color: microphoneController.testing ? "#20B8AE" : "#27313D"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: microphoneController.testing ? "Listening" : "Microphone test"
                            color: "#F4F1E8"
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                        }

                        Text {
                            text: microphoneController.status
                            color: "#8490A0"
                            font.pixelSize: 13
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 12
                        Layout.preferredHeight: 12
                        radius: 6
                        color: microphoneController.testing ? "#20B8AE" : "#536170"
                    }
                }

                Rectangle {
                    id: meterTrack
                    Layout.fillWidth: true
                    implicitHeight: 18
                    radius: 9
                    color: "#202A34"
                    clip: true

                    Rectangle {
                        width: meterTrack.width * microphoneController.inputLevel
                        height: parent.height
                        radius: 9
                        color: "#20B8AE"

                        Behavior on width {
                            NumberAnimation {
                                duration: 80
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: "Input level"
                        color: "#667180"
                        font.pixelSize: 12
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Text {
                        text: Math.round(microphoneController.inputLevel * 100) + "%"
                        color: "#9FE8DF"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                }

                Button {
                    id: testButton
                    Layout.alignment: Qt.AlignHCenter
                    implicitWidth: 180
                    implicitHeight: 46
                    text: microphoneController.testing ? "Stop test" : "Test microphone"
                    enabled: microphoneController.hasMicrophone
                    hoverEnabled: true

                    contentItem: Text {
                        text: testButton.text
                        color: "#F4F1E8"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 12
                        color: testButton.hovered ? "#26313B" : "#1C252E"
                        border.width: 1
                        border.color: microphoneController.testing ? "#20B8AE" : "#384553"
                    }

                    onClicked: {
                        if (microphoneController.testing) {
                            microphoneController.stopTest()
                        } else {
                            microphoneController.startTest()
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 62
            radius: 12
            color: "#132825"
            border.width: 1
            border.color: "#20564F"

            Text {
                anchors.fill: parent
                anchors.margins: 14
                text: "Bluetooth and USB microphones are updated automatically when connected or removed."
                color: "#9FE8DF"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                verticalAlignment: Text.AlignVCenter
            }
        }

        Item {
            Layout.fillHeight: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Button {
                id: backButton
                implicitWidth: 110
                implicitHeight: 48
                text: "Back"
                flat: true
                hoverEnabled: true

                contentItem: Text {
                    text: backButton.text
                    color: backButton.hovered ? "#F4F1E8" : "#98A2B3"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 12
                    color: backButton.hovered ? "#1A222C" : "transparent"
                    border.width: 1
                    border.color: "#303A46"
                }

                onClicked: microphonePage.backRequested()
            }

            Item {
                Layout.fillWidth: true
            }

            Text {
                text: "Step 4 of 5"
                color: "#667180"
                font.pixelSize: 12
            }

            PrimaryButton {
                text: "Continue"
                enabled: microphoneController.hasMicrophone
                         && !microphoneController.testing
                onClicked: microphonePage.continueRequested()
            }
        }
    }
}
