import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: setupScreen

    signal backRequested()
    signal setupFinished()
    property int currentStep: 0

    Component.onCompleted: {
        setupController.scanSystem()
        cudaController.scan()
    }

    component NavigationItem: Rectangle {
        property int stepNumber: 1
        property string stepTitle: ""
        property bool active: false
        property bool completed: false

        Layout.fillWidth: true
        implicitHeight: 48
        radius: 12
        color: active ? "#1B292D" : "transparent"

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 26
                Layout.preferredHeight: 26
                radius: 13
                color: completed ? "#20B8AE" : (active ? "#193F3C" : "#242C36")
                border.width: active ? 1 : 0
                border.color: "#20B8AE"

                Text {
                    anchors.centerIn: parent
                    text: completed ? "✓" : stepNumber
                    color: completed ? "#071311" : (active ? "#9FE8DF" : "#7D8998")
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
            }

            Text {
                Layout.fillWidth: true
                text: stepTitle
                color: active ? "#F4F1E8" : "#7D8998"
                font.pixelSize: 14
                font.weight: active ? Font.DemiBold : Font.Normal
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            color: "#10151C"
            border.width: 1
            border.color: "#1D2630"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 8

                Text {
                    text: "Setup"
                    color: "#F4F1E8"
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    Layout.bottomMargin: 16
                }

                NavigationItem {
                    stepNumber: 1
                    stepTitle: "System check"
                    active: setupScreen.currentStep === 0
                    completed: setupScreen.currentStep > 0
                }

                NavigationItem {
                    stepNumber: 2
                    stepTitle: "Speech model"
                    active: setupScreen.currentStep === 1
                    completed: setupScreen.currentStep > 1
                }

                NavigationItem {
                    stepNumber: 3
                    stepTitle: "LM Studio"
                    active: setupScreen.currentStep === 2
                    completed: setupScreen.currentStep > 2
                }

                NavigationItem {
                    stepNumber: 4
                    stepTitle: "Microphone"
                    active: setupScreen.currentStep === 3
                    completed: setupScreen.currentStep > 3
                }

                NavigationItem {
                    stepNumber: 5
                    stepTitle: "Ready"
                    active: setupScreen.currentStep === 4
                }

                Item {
                    Layout.fillHeight: true
                }

                Text {
                    Layout.fillWidth: true
                    text: "Your audio stays on this device."
                    color: "#667180"
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: setupScreen.currentStep

            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 46
                    anchors.rightMargin: 46
                    anchors.topMargin: 28
                    anchors.bottomMargin: 26
                    spacing: 14

                    Text {
                        text: "System check"
                        color: "#F4F1E8"
                        font.pixelSize: 32
                        font.weight: Font.Bold
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Let's make sure your computer is ready for fast local dictation."
                        color: "#98A2B3"
                        font.pixelSize: 16
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        BusyIndicator {
                            Layout.preferredWidth: 24
                            Layout.preferredHeight: 24
                            visible: setupController.scanning
                            running: setupController.scanning
                            palette.highlight: "#20B8AE"
                        }

                        Text {
                            Layout.fillWidth: true
                            text: setupController.scanning
                                  ? "Checking your system..."
                                  : setupController.systemSummary
                            color: "#7F8A99"
                            font.pixelSize: 13
                        }

                        Button {
                            id: scanButton
                            visible: !setupController.scanning
                            text: "Scan again"
                            flat: true

                            contentItem: Text {
                                text: scanButton.text
                                color: "#20B8AE"
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            onClicked: {
                                setupController.scanSystem()
                                cudaController.scan()
                            }
                        }
                    }

                    ListView {
                        id: checkList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10
                        clip: true
                        model: setupController.checks

                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                        }

                        delegate: Rectangle {
                            required property var modelData

                            readonly property bool cudaCard:
                                modelData.key === "cuda_runtime"
                            readonly property bool cardReady:
                                cudaCard ? cudaController.ready : modelData.ready
                            readonly property string cardDescription:
                                cudaCard ? cudaController.message : modelData.description
                            readonly property string cardStatus:
                                cudaCard ? cudaController.status : modelData.status

                            width: checkList.width
                            height: cudaCard ? 112 : (modelData.action === "" ? 82 : 104)
                            radius: 14
                            color: "#151B23"
                            border.width: 1
                            border.color: cardReady ? "#245A53" : "#554B32"

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 14

                                Rectangle {
                                    Layout.preferredWidth: 38
                                    Layout.preferredHeight: 38
                                    radius: 12
                                    color: cardReady ? "#14332F" : "#302B1E"

                                    Text {
                                        anchors.centerIn: parent
                                        text: cardReady ? "✓" : "!"
                                        color: cardReady ? "#20B8AE" : "#C7A96B"
                                        font.pixelSize: 17
                                        font.weight: Font.Bold
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3

                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.title
                                        color: "#F4F1E8"
                                        font.pixelSize: 15
                                        font.weight: Font.DemiBold
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: cardDescription
                                        color: "#8490A0"
                                        font.pixelSize: 13
                                        elide: Text.ElideRight
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        visible: cudaCard
                                                 ? cudaController.errorMessage !== ""
                                                 : modelData.action !== ""
                                        text: cudaCard
                                              ? cudaController.errorMessage
                                              : modelData.action
                                        color: "#C7A96B"
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                    }
                                }

                                ColumnLayout {
                                    spacing: 8

                                    Text {
                                        Layout.alignment: Qt.AlignRight
                                        text: cardStatus
                                        color: cardReady ? "#79D8CE" : "#D2BB83"
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                    }

                                    Button {
                                        id: cudaSetupButton
                                        visible: cudaCard && !cardReady
                                        enabled: cudaController.canInstall
                                        text: cudaController.installing
                                              ? "Installing..."
                                              : "Set up automatically"

                                        contentItem: Text {
                                            text: cudaSetupButton.text
                                            color: cudaSetupButton.enabled
                                                   ? "#9FE8DF"
                                                   : "#667180"
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }

                                        background: Rectangle {
                                            radius: 10
                                            color: cudaSetupButton.hovered
                                                   ? "#193F3C"
                                                   : "#132825"
                                            border.width: 1
                                            border.color: cudaSetupButton.enabled
                                                          ? "#20564F"
                                                          : "#27313D"
                                        }

                                        onClicked: cudaController.install()
                                    }
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

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

                            onClicked: setupScreen.backRequested()
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Step 1 of 5"
                            color: "#667180"
                            font.pixelSize: 12
                        }

                        PrimaryButton {
                            text: "Continue"
                            enabled: !setupController.scanning
                                     && !setupController.hasBlockingIssues
                            onClicked: setupScreen.currentStep = 1
                        }
                    }
                }
            }

            SpeechModelPage {
                onBackRequested: setupScreen.currentStep = 0
                onContinueRequested: setupScreen.currentStep = 2
            }

            LMStudioPage {
                onBackRequested: setupScreen.currentStep = 1
                onContinueRequested: setupScreen.currentStep = 3
            }

            MicrophonePage {
                onBackRequested: setupScreen.currentStep = 2
                onContinueRequested: setupScreen.currentStep = 4
            }

            ReadyPage {
                onBackRequested: setupScreen.currentStep = 3
                onFinishRequested: setupScreen.setupFinished()
            }
        }
    }
}
