import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "components"
import "pages"

ApplicationWindow {
    id: root

    property bool setupStarted: false
    property bool mainStarted: false

    width: 1100
    height: 720
    minimumWidth: 860
    minimumHeight: 600
    visible: true
    title: "KoeScribe"
    color: "#0D1117"

    Component.onCompleted: {
        root.mainStarted = setupController.setupComplete
    }

    component FeatureItem: Row {
        property string label: ""
        spacing: 8

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: "#20B8AE"
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: parent.label
            color: "#AAB2C0"
            font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#0D1117"

        Rectangle {
            visible: !root.setupStarted && !root.mainStarted
            width: 420
            height: 420
            radius: 210
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: -210
            anchors.bottomMargin: -210
            color: "#101E21"
        }

        RowLayout {
            id: topNavigation
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 32
            anchors.rightMargin: 32
            anchors.topMargin: 24
            height: 52
            spacing: 12

            Image {
                source: "assets/koescribe-icon.png"
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                Layout.alignment: Qt.AlignVCenter
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            Text {
                text: "KoeScribe"
                color: "#F4F1E8"
                font.pixelSize: 20
                font.weight: Font.Bold
                Layout.alignment: Qt.AlignVCenter
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                Layout.preferredWidth: 112
                Layout.preferredHeight: 36
                Layout.alignment: Qt.AlignVCenter
                radius: 18
                color: "#132825"
                border.width: 1
                border.color: "#20564F"

                Row {
                    anchors.centerIn: parent
                    spacing: 7

                    Rectangle {
                        width: 7
                        height: 7
                        radius: 4
                        color: "#20B8AE"
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "100% Local"
                        color: "#9FE8DF"
                        font.pixelSize: 12
                        font.weight: Font.Medium
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        ColumnLayout {
            visible: !root.setupStarted && !root.mainStarted
            width: Math.min(660, root.width - 100)
            anchors.centerIn: parent
            spacing: 22

            Image {
                source: "assets/koescribe-icon.png"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 112
                Layout.preferredHeight: 112
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            Text {
                Layout.fillWidth: true
                Layout.topMargin: 8
                text: "Speak naturally.\nWrite anywhere."
                color: "#F4F1E8"
                font.pixelSize: 48
                font.weight: Font.Bold
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.05
            }

            Text {
                Layout.fillWidth: true
                Layout.maximumWidth: 580
                Layout.alignment: Qt.AlignHCenter
                text: "Fast, private voice dictation powered by faster-whisper and your local LM Studio model."
                color: "#98A2B3"
                font.pixelSize: 17
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                lineHeight: 1.35
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 8
                spacing: 24
                FeatureItem { label: "Private" }
                FeatureItem { label: "Fast" }
                FeatureItem { label: "Offline" }
            }

            PrimaryButton {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 18
                text: "Start setup"
                onClicked: root.setupStarted = true
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 4
                text: "Takes about 2 minutes"
                color: "#667180"
                font.pixelSize: 12
            }
        }

        Text {
            visible: !root.setupStarted && !root.mainStarted
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            text: "KoeScribe 0.1.0"
            color: "#4F5B6B"
            font.pixelSize: 11
        }

        SetupScreen {
            visible: root.setupStarted && !root.mainStarted
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: topNavigation.bottom
            anchors.bottom: parent.bottom
            anchors.topMargin: 16

            onBackRequested: root.setupStarted = false
            onSetupFinished: {
                root.setupStarted = false
                root.mainStarted = true
            }
        }

        MainDictationPage {
            visible: root.mainStarted
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: topNavigation.bottom
            anchors.bottom: parent.bottom
            anchors.topMargin: 8

            onSettingsRequested: {
                setupController.resetSetup()
                root.mainStarted = false
                root.setupStarted = true
            }
        }
    }
}
