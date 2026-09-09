import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: lmStudioPage

    signal backRequested()
    signal continueRequested()

    Component.onCompleted: {
        setupController.checkLmStudio(
            setupController.lmStudioUrl
        )
    }

    ScrollView {
        id: pageScroll
        anchors.fill: parent
        anchors.leftMargin: 46
        anchors.rightMargin: 46
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        clip: true
        contentWidth: availableWidth

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AsNeeded

        ColumnLayout {
            width: pageScroll.availableWidth
            spacing: 14

        Text {
            text: "Connect LM Studio"
            color: "#F4F1E8"

            font.pixelSize: 32
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true

            text: "LM Studio improves punctuation, removes filler words and formats your transcription. All processing remains on your computer."
            color: "#98A2B3"

            font.pixelSize: 16
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 176

            radius: 14
            color: "#151B23"

            border.width: 1
            border.color: "#27313D"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18

                spacing: 10

                Text {
                    text: "LM Studio setup"
                    color: "#F4F1E8"

                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Repeater {
                    model: [
                        "Open LM Studio and download a small instruct model.",
                        "Open the Developer tab.",
                        "Load your downloaded model.",
                        "Start the Local Server."
                    ]

                    delegate: RowLayout {
                        required property string modelData
                        required property int index

                        Layout.fillWidth: true
                        spacing: 10

                        Rectangle {
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22

                            radius: 11
                            color: "#193F3C"

                            Text {
                                anchors.centerIn: parent

                                text: index + 1
                                color: "#79D8CE"

                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                        }

                        Text {
                            Layout.fillWidth: true

                            text: modelData
                            color: "#AAB2C0"

                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        Text {
            text: "Server address"
            color: "#D5D9E0"

            font.pixelSize: 13
            font.weight: Font.DemiBold
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            TextField {
                id: urlField

                Layout.fillWidth: true
                implicitHeight: 48

                text: setupController.lmStudioUrl
                placeholderText: "http://127.0.0.1:1234/v1"

                color: "#F4F1E8"
                placeholderTextColor: "#667180"

                selectByMouse: true

                background: Rectangle {
                    radius: 12
                    color: "#111820"

                    border.width: urlField.activeFocus ? 2 : 1

                    border.color: urlField.activeFocus
                                  ? "#20B8AE"
                                  : "#303A46"
                }
            }

            Button {
                id: testButton

                implicitWidth: 150
                implicitHeight: 48

                text: setupController.lmStudioChecking
                      ? "Connecting..."
                      : "Test connection"

                enabled: !setupController.lmStudioChecking
                hoverEnabled: true

                contentItem: Text {
                    text: testButton.text

                    color: testButton.enabled
                           ? "#F4F1E8"
                           : "#667180"

                    font.pixelSize: 13
                    font.weight: Font.DemiBold

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 12

                    color: testButton.hovered
                           ? "#26313B"
                           : "#1C252E"

                    border.width: 1
                    border.color: "#384553"
                }

                onClicked: {
                    setupController.checkLmStudio(
                        urlField.text
                    )
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 82

            radius: 14

            color: setupController.lmStudioConnected
                   ? "#132825"
                   : "#201C19"

            border.width: 1

            border.color: setupController.lmStudioConnected
                          ? "#20564F"
                          : "#51412E"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16

                spacing: 14

                Rectangle {
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38

                    radius: 12

                    color: setupController.lmStudioConnected
                           ? "#14332F"
                           : "#302B1E"

                    Text {
                        anchors.centerIn: parent

                        text: setupController.lmStudioConnected
                              ? "✓"
                              : "!"

                        color: setupController.lmStudioConnected
                               ? "#20B8AE"
                               : "#C7A96B"

                        font.pixelSize: 18
                        font.weight: Font.Bold
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        Layout.fillWidth: true

                        text: setupController.lmStudioStatus
                        color: "#F4F1E8"

                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }

                    Text {
                        Layout.fillWidth: true

                        text: setupController.lmStudioMessage
                        color: "#8490A0"

                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                }

                BusyIndicator {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28

                    visible: setupController.lmStudioChecking
                    running: setupController.lmStudioChecking

                    palette.highlight: "#20B8AE"
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            visible: (
                setupController.lmStudioConnected
                && setupController.lmStudioModels.length > 0
                && setupController.lmStudioEnabled
            )

            Text {
                text: "Text cleanup model"
                color: "#D5D9E0"

                font.pixelSize: 13
                font.weight: Font.DemiBold
            }

            ComboBox {
                id: modelSelector

                Layout.fillWidth: true
                implicitHeight: 48

                model: setupController.lmStudioModels
                textRole: "name"
                valueRole: "model_id"

                onActivated: {
                    setupController.selectLmStudioModel(
                        currentValue
                    )
                }

                Component.onCompleted: {
                    if (count > 0) {
                        currentIndex = 0
                    }
                }
            }
        }

        CheckBox {
            id: enableLmStudio

            text: "Use LM Studio to clean and format transcriptions"
            checked: setupController.lmStudioEnabled

            onToggled: {
                setupController.setLmStudioEnabled(
                    checked
                )
            }

            contentItem: Text {
                leftPadding: enableLmStudio.indicator.width + 10

                text: enableLmStudio.text
                color: "#D5D9E0"

                font.pixelSize: 13
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            Layout.fillWidth: true

            visible: !setupController.lmStudioEnabled

            text: "You can continue without LM Studio. KoeScribe will insert the raw faster-whisper transcription."
            color: "#C7A96B"

            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 6
            Layout.bottomMargin: 4
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

                    color: backButton.hovered
                           ? "#F4F1E8"
                           : "#98A2B3"

                    font.pixelSize: 14
                    font.weight: Font.DemiBold

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 12

                    color: backButton.hovered
                           ? "#1A222C"
                           : "transparent"

                    border.width: 1
                    border.color: "#303A46"
                }

                onClicked: {
                    lmStudioPage.backRequested()
                }
            }

            Item {
                Layout.fillWidth: true
            }

            Text {
                text: "Step 3 of 5"
                color: "#667180"
                font.pixelSize: 12
            }

            PrimaryButton {
                text: setupController.lmStudioEnabled
                      ? "Continue"
                      : "Continue without AI"

                enabled: (
                    !setupController.lmStudioChecking
                    && setupController.lmStudioReady
                )

                onClicked: {
                    lmStudioPage.continueRequested()
                }
            }
        }
        }
    }
}
